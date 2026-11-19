import pandas as pd
import numpy as np
from tqdm import tqdm
from sqlalchemy import text

from database.connection import get_engine, get_db_connection_cm
from config.logger import log
from config.constants import FREQUENCIES
from config.db_table import ASSET_TABLE_CONFIG


LEFT = 3
RIGHT = 3
BATCH_SIZE = 5000


# =========================================================
# CLEANER
# =========================================================
def clean(v):
    if v is None:
        return None
    if isinstance(v, (np.floating, np.integer)):
        return v.item()
    return v


def sanitize_row(row):
    return tuple(clean(x) for x in row)


# =========================================================
# LOAD DATA (SAFE + CONSISTENT)
# =========================================================
def load_price_data(engine, price_table, timeframe):

    log(f"📥 LOAD | {price_table} | TF={timeframe}")

    query = text(f"""
        SELECT symbol_id,
               date,
               COALESCE(adj_close, close) AS close,
               volume
        FROM {price_table}
        WHERE timeframe = :timeframe
        ORDER BY symbol_id, date
    """)

    with engine.connect() as conn:
        df = pd.read_sql(query, conn, params={"timeframe": timeframe})

    df = df.dropna(subset=["close"])

    log(f"✅ rows={len(df)} symbols={df['symbol_id'].nunique()}")

    return df


# =========================================================
# PIVOTS (STRICT SCHEMA)
# =========================================================
def detect_pivots(df, timeframe):

    pivots = []

    for symbol_id, g in df.groupby("symbol_id"):

        g = g.sort_values("date")
        prices = g["close"].values

        if len(prices) < LEFT + RIGHT + 1:
            continue

        for i in range(LEFT, len(prices) - RIGHT):

            window = prices[i-LEFT:i+RIGHT+1]

            price = prices[i]
            date = g.iloc[i]["date"]

            if np.isnan(price):
                continue

            # HIGH PIVOT
            if price == window.max():
                pivots.append((
                    symbol_id,
                    timeframe,
                    date,
                    "H",
                    float(price),
                    LEFT,
                    RIGHT
                ))

            # LOW PIVOT
            elif price == window.min():
                pivots.append((
                    symbol_id,
                    timeframe,
                    date,
                    "L",
                    float(price),
                    LEFT,
                    RIGHT
                ))

    log(f"📍 pivots={len(pivots)}")
    return pivots


# =========================================================
# CONTRACTIONS (SAFE)
# =========================================================
def build_contractions(pivots, timeframe):

    df = pd.DataFrame(pivots, columns=[
        "symbol_id","timeframe","date","pivot_type","price","left","right"
    ])

    lows = df[df["pivot_type"] == "L"]

    contractions = []

    for symbol_id, g in lows.groupby("symbol_id"):

        g = g.sort_values("date")

        for i in range(1, len(g)):

            prev = g.iloc[i-1]
            curr = g.iloc[i]

            prev_price = float(prev.price)
            curr_price = float(curr.price)

            if prev_price == 0:
                continue

            pct = (curr_price - prev_price) / prev_price

            contractions.append((
                symbol_id,
                timeframe,
                prev.date,
                prev_price,
                curr.date,
                curr_price,
                float(pct),
                (curr.date - prev.date).days if prev.date and curr.date else None,
                None
            ))

    log(f"📉 contractions={len(contractions)}")
    return contractions


# =========================================================
# PATTERNS
# =========================================================
def build_patterns(contractions, timeframe):

    df = pd.DataFrame(contractions, columns=[
        "symbol_id","timeframe",
        "high_date","high_price",
        "low_date","low_price",
        "pct","duration","vol"
    ])

    patterns = []

    for symbol_id, g in df.groupby("symbol_id"):

        g = g.sort_values("low_date")

        if len(g) < 2:
            continue

        pcts = g["pct"].tail(3).values

        patterns.append((
            symbol_id,
            timeframe,
            g["high_date"].iloc[0],
            g["low_date"].iloc[-1],
            len(g),
            float(pcts[0]) if len(pcts)>0 else None,
            float(pcts[1]) if len(pcts)>1 else None,
            float(pcts[2]) if len(pcts)>2 else None,
            True,
            False,
            True,
            None,
            None
        ))

    log(f"🧩 patterns={len(patterns)}")
    return patterns


# =========================================================
# SIGNALS (SAFE BREAKOUT LOGIC)
# =========================================================
def build_signals(patterns, df, timeframe):

    signals = []

    df = df.sort_values(["symbol_id","date"])

    for symbol_id, g in df.groupby("symbol_id"):

        if len(g) < 25:
            continue

        resistance = g["close"].iloc[-21:-1].max()
        last_close = g["close"].iloc[-1]

        if last_close > resistance:

            signals.append((
                symbol_id,
                timeframe,
                g["date"].iloc[-1],
                float(last_close),
                None,
                None,
                "BREAKOUT",
                True
            ))

    log(f"⚡ signals={len(signals)}")
    return signals


# =========================================================
# BULK INSERT (ROBUST)
# =========================================================
def bulk_insert(conn, query, data, label):

    if not data:
        log(f"⚠️ skip {label}")
        return

    cur = conn.cursor()

    for i in tqdm(range(0, len(data), BATCH_SIZE), desc=label):

        batch = [sanitize_row(r) for r in data[i:i+BATCH_SIZE]]
        cur.executemany(query, batch)

    conn.commit()

    log(f"✅ inserted {label}")


# =========================================================
# ENGINE (FINAL CLEAN)
# =========================================================
def run_vcp_engine(asset_type):

    engine = get_engine()
    cfg = ASSET_TABLE_CONFIG[asset_type]

    price_table = cfg["price"]
    vcp = cfg["vcp"]

    log(f"🚀 START VCP | {asset_type}")

    for tf in FREQUENCIES:

        log(f"\n==== TF={tf} ====")

        df = load_price_data(engine, price_table, tf)

        if df.empty:
            log("⚠️ empty df")
            continue

        pivots = detect_pivots(df, tf)
        if not pivots:
            continue

        contractions = build_contractions(pivots, tf)
        if not contractions:
            continue

        patterns = build_patterns(contractions, tf)
        if not patterns:
            continue

        signals = build_signals(patterns, df, tf)

        with get_db_connection_cm() as conn:

            bulk_insert(conn,
                f"""
                INSERT INTO {vcp['pivot']}
                (symbol_id, timeframe, date, pivot_type, price, left_bars, right_bars)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT DO NOTHING
                """,
                pivots,
                "PIVOTS"
            )

            bulk_insert(conn,
                f"""
                INSERT INTO {vcp['contraction']}
                (symbol_id, timeframe, high_date, high_price,
                 low_date, low_price,
                 contraction_pct, duration_days, avg_volume)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                contractions,
                "CONTRACTIONS"
            )

            bulk_insert(conn,
                f"""
                INSERT INTO {vcp['pattern']}
                (symbol_id, timeframe, start_date, end_date,
                 num_contractions,
                 contraction_1, contraction_2, contraction_3,
                 range_tightening, volume_contracting, is_valid,
                 resistance_level, pivot_price)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                patterns,
                "PATTERNS"
            )

            bulk_insert(conn,
                f"""
                INSERT INTO {vcp['signal']}
                (symbol_id, timeframe, date,
                 breakout_price, breakout_volume, volume_ratio,
                 signal_type, is_triggered)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                signals,
                "SIGNALS"
            )

    log(f"🎯 DONE | {asset_type}")