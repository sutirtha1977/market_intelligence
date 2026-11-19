import pandas as pd
from tqdm import tqdm
from datetime import date, timedelta
from typing import Optional, Tuple

from config.logger import log
from database.connection import get_db_connection_cm, get_engine
from config.db_table import FNO_TABLE_MAP

from py_vollib.black_scholes.implied_volatility import implied_volatility
from py_vollib.black_scholes.greeks.analytical import delta, gamma, theta, vega

RISK_FREE_RATE = 0.065

# --------------------------------------------------------------------------
def time_to_expiry(trade_date: date, expiry_date: date) -> float:
    return max((expiry_date - trade_date).days, 0) / 365.0

# --------------------------------------------------------------------------
def compute_greeks_row(row) -> Optional[Tuple]:
    try:
        T = time_to_expiry(row.trade_date, row.expiry_date)
        if T <= 0:
            return None

        if (
            row.close_price is None
            or row.underlying_price is None
            or row.strike_price is None
            or row.close_price <= 0
            or row.underlying_price <= 0
            or row.strike_price <= 0
        ):
            return None

        flag = "c" if row.option_type == "CE" else "p"

        iv = implied_volatility(
            float(row.close_price),
            float(row.underlying_price),
            float(row.strike_price),
            T,
            RISK_FREE_RATE,
            flag
        )

        if iv is None or iv <= 0:
            return None

        d = delta(flag, row.underlying_price, row.strike_price, T, RISK_FREE_RATE, iv)
        g_val = gamma(flag, row.underlying_price, row.strike_price, T, RISK_FREE_RATE, iv)
        t_val = theta(flag, row.underlying_price, row.strike_price, T, RISK_FREE_RATE, iv)
        v_val = vega(flag, row.underlying_price, row.strike_price, T, RISK_FREE_RATE, iv)

        if d is None or g_val is None or t_val is None or v_val is None:
            return None

        return (
            row.trade_date,
            row.symbol,
            row.expiry_date,
            float(row.strike_price),
            row.option_type,
            float(iv),
            float(d),
            float(g_val),
            float(t_val),
            float(v_val),
        )

    except Exception:
        return None

# --------------------------------------------------------------------------
def update_options_greeks(options_table: str, start_date: date, end_date: date):

    greeks_table = f"{options_table}_greeks"

    log(f"▶️ Greeks START | {options_table} | {start_date} → {end_date}")

    engine = get_engine()

    with get_db_connection_cm() as conn:
        with conn.cursor() as cur:

            # ----------------------------------------------------------
            # SYMBOL + EXPIRY COMBINATIONS
            # ----------------------------------------------------------
            cur.execute(f"""
                SELECT DISTINCT symbol, expiry_date
                FROM {options_table}
                WHERE trade_date BETWEEN %s AND %s
                ORDER BY symbol, expiry_date
            """, (start_date, end_date))

            combos = cur.fetchall()

            if not combos:
                log(f"⚠️ No data in {options_table}")
                return

            total_rows = 0

            # ----------------------------------------------------------
            # LOOP
            # ----------------------------------------------------------
            for symbol, expiry in tqdm(combos, desc=options_table, ncols=110):

                df = pd.read_sql(f"""
                    SELECT
                        trade_date,
                        symbol,
                        expiry_date,
                        strike_price,
                        option_type,
                        close_price,
                        underlying_price
                    FROM {options_table}
                    WHERE symbol = %s
                      AND expiry_date = %s
                      AND trade_date BETWEEN %s AND %s
                    ORDER BY trade_date, strike_price
                """, engine, params=(symbol, expiry, start_date, end_date))

                if df.empty:
                    continue

                results = []

                for row in df.itertuples(index=False):
                    res = compute_greeks_row(row)
                    if res:
                        results.append(res)

                if not results:
                    continue

                insert_sql = f"""
                    INSERT INTO {greeks_table} (
                        trade_date, symbol, expiry_date, strike_price, option_type,
                        implied_volatility, delta, gamma, theta, vega
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (trade_date, symbol, expiry_date, strike_price, option_type)
                    DO UPDATE SET
                        implied_volatility = EXCLUDED.implied_volatility,
                        delta = EXCLUDED.delta,
                        gamma = EXCLUDED.gamma,
                        theta = EXCLUDED.theta,
                        vega = EXCLUDED.vega;
                """

                cur.executemany(insert_sql, results)
                conn.commit()

                total_rows += len(results)

            log(f"✅ Greeks DONE | {options_table} | rows={total_rows}")


# --------------------------------------------------------------------------
def update_all_options_greeks():

    log("🚀 Greeks pipeline START (AUTO INCREMENTAL)")

    stock_table = FNO_TABLE_MAP["stock"][0]
    index_table = FNO_TABLE_MAP["index"][0]

    with get_db_connection_cm() as conn:
        with conn.cursor() as cur:

            for table in [stock_table, index_table]:

                greeks_table = f"{table}_greeks"

                # --------------------------------------------------
                # SOURCE RANGE
                # --------------------------------------------------
                cur.execute(f"""
                    SELECT MIN(trade_date), MAX(trade_date)
                    FROM {table}
                """)
                src_min, src_max = cur.fetchone()

                if not src_min or not src_max:
                    log(f"⚠️ No source data in {table}")
                    continue

                # --------------------------------------------------
                # LAST PROCESSED
                # --------------------------------------------------
                cur.execute(f"""
                    SELECT MAX(trade_date)
                    FROM {greeks_table}
                """)
                last_done = cur.fetchone()[0]

                # --------------------------------------------------
                # START DATE LOGIC
                # --------------------------------------------------
                if last_done:
                    start_date = last_done + timedelta(days=1)
                else:
                    start_date = src_min

                end_date = src_max

                # --------------------------------------------------
                # SKIP IF UP-TO-DATE
                # --------------------------------------------------
                if start_date > end_date:
                    log(f"✅ {table} already up-to-date (last={last_done})")
                    continue

                log(f"📌 Processing {table} | {start_date} → {end_date}")

                update_options_greeks(table, start_date, end_date)

    log("🎉 Greeks pipeline COMPLETE")
# --------------------------------------------------------------------------