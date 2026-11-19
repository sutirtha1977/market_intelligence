import pandas as pd
from typing import Optional, Tuple, List
from tqdm import tqdm

from database.connection import (
    get_db_connection,
    close_db_connection,
    get_engine 
)
from config.logger import log
from config.db_config import FNO_TABLE_MAP

# --------------------------------------------------------------------------
def calculate_expiry_metrics(df: pd.DataFrame) -> Optional[Tuple]:
    if df.empty:
        return None

    # TOTAL OI
    total_call_oi = df[df["option_type"] == "CE"]["open_interest"].sum()
    total_put_oi = df[df["option_type"] == "PE"]["open_interest"].sum()

    # OI CLUSTERS (Top 3)
    call_df = (
        df[df["option_type"] == "CE"]
        .groupby("strike_price")["open_interest"]
        .sum()
        .nlargest(3)
        .reset_index()
    )

    put_df = (
        df[df["option_type"] == "PE"]
        .groupby("strike_price")["open_interest"]
        .sum()
        .nlargest(3)
        .reset_index()
    )

    if call_df.empty or put_df.empty:
        return None

    call_low, call_high = call_df["strike_price"].min(), call_df["strike_price"].max()
    put_low, put_high = put_df["strike_price"].min(), put_df["strike_price"].max()

    # MAX PAIN (optimized)
    strikes = df["strike_price"].unique()

    pain_values = []
    grouped = df.groupby(["strike_price", "option_type"])["open_interest"].sum().reset_index()

    for s in strikes:
        ce_pain = ((s - grouped["strike_price"]).clip(lower=0) *
                   grouped["open_interest"] * (grouped["option_type"] == "CE")).sum()

        pe_pain = ((grouped["strike_price"] - s).clip(lower=0) *
                   grouped["open_interest"] * (grouped["option_type"] == "PE")).sum()

        pain_values.append((s, ce_pain + pe_pain))

    max_pain = min(pain_values, key=lambda x: x[1])[0]

    return (
        float(max_pain),
        int(total_call_oi),
        int(total_put_oi),
        float(call_low),
        float(call_high),
        float(put_low),
        float(put_high),
    )


# --------------------------------------------------------------------------
def update_expiry_metrics(asset_type: str):
    options_table = FNO_TABLE_MAP[asset_type][0]
    metrics_table = FNO_TABLE_MAP[asset_type][6]

    log(f"📌 EXPIRY METRICS START | {asset_type.upper()}")

    conn = get_db_connection()       
    engine = get_engine()              
    cur = conn.cursor()

    try:
        # ----------------------------------------------------------
        # GET MISSING COMBINATIONS (incremental)
        # ----------------------------------------------------------
        combos_df = pd.read_sql(f"""
            SELECT DISTINCT o.trade_date, o.symbol, o.expiry_date
            FROM {options_table} o
            LEFT JOIN {metrics_table} m
              ON o.trade_date = m.trade_date
             AND o.symbol = m.symbol
             AND o.expiry_date = m.expiry_date
            WHERE m.trade_date IS NULL
            ORDER BY o.trade_date
        """, engine)

        if combos_df.empty:
            log(f"✅ {asset_type.upper()} expiry metrics already up-to-date")
            return

        log(f"📊 Pending rows: {len(combos_df):,}")

        batch_data: List[Tuple] = []
        batch_size = 500  

        # ----------------------------------------------------------
        # LOOP
        # ----------------------------------------------------------
        for _, row in tqdm(
            combos_df.iterrows(),
            total=len(combos_df),
            desc=f"{asset_type.upper()} EXPIRY",
            ncols=110
        ):
            trade_date = row["trade_date"]
            symbol = row["symbol"]
            expiry = row["expiry_date"]

            df = pd.read_sql(f"""
                SELECT strike_price, option_type, open_interest
                FROM {options_table}
                WHERE trade_date = %s
                  AND symbol = %s
                  AND expiry_date = %s
            """, engine, params=(trade_date, symbol, expiry))

            result = calculate_expiry_metrics(df)

            if not result:
                continue

            batch_data.append((
                trade_date,
                symbol,
                expiry,
                *result
            ))

            # ------------------------------------------------------
            # BATCH INSERT
            # ------------------------------------------------------
            if len(batch_data) >= batch_size:
                _bulk_upsert(cur, metrics_table, batch_data)
                batch_data.clear()

        # FINAL FLUSH
        if batch_data:
            _bulk_upsert(cur, metrics_table, batch_data)

        conn.commit()

        log(f"✅ EXPIRY METRICS DONE | {asset_type.upper()}")

    except Exception as e:
        conn.rollback()
        log(f"❌ EXPIRY METRICS FAILED | {asset_type.upper()} | {e}")
        raise

    finally:
        close_db_connection(conn)

# --------------------------------------------------------------------------
def _bulk_upsert(cur, table: str, rows: List[Tuple]):
    """
    Fast batch upsert
    """
    from psycopg2.extras import execute_values

    query = f"""
        INSERT INTO {table} (
            trade_date,
            symbol,
            expiry_date,
            max_pain_strike,
            total_call_oi,
            total_put_oi,
            call_oi_cluster_low,
            call_oi_cluster_high,
            put_oi_cluster_low,
            put_oi_cluster_high
        )
        VALUES %s
        ON CONFLICT (trade_date, symbol, expiry_date)
        DO UPDATE SET
            max_pain_strike = EXCLUDED.max_pain_strike,
            total_call_oi = EXCLUDED.total_call_oi,
            total_put_oi = EXCLUDED.total_put_oi,
            call_oi_cluster_low = EXCLUDED.call_oi_cluster_low,
            call_oi_cluster_high = EXCLUDED.call_oi_cluster_high,
            put_oi_cluster_low = EXCLUDED.put_oi_cluster_low,
            put_oi_cluster_high = EXCLUDED.put_oi_cluster_high;
    """

    execute_values(cur, query, rows)

# --------------------------------------------------------------------------
def update_all_expiry_metrics():
    log("🚀 EXPIRY METRICS PIPELINE START")

    for asset in ["stock", "index"]:
        try:
            update_expiry_metrics(asset)
        except Exception as e:
            log(f"❌ Failed for {asset.upper()} | {e}")

    log("🎉 EXPIRY METRICS PIPELINE COMPLETE")
# --------------------------------------------------------------------------