from config.logger import log
from database.connection import get_db_connection_cm

# --------------------------------------------------------------------------
FNO_ROUTE_MAP = {
    "STF": {
        "table": "fno_stock_futures",
        "kind": "FUT"
    },
    "IDF": {
        "table": "fno_index_futures",
        "kind": "FUT"
    },
    "STO": {
        "table": "fno_stock_options",
        "kind": "OPT"
    },
    "IDO": {
        "table": "fno_index_options",
        "kind": "OPT"
    }
}

# --------------------------------------------------------------------------
FUTURES_SQL = """
INSERT INTO {table} (
    trade_date,
    timeframe,
    instrument_type,
    symbol,
    expiry_date,
    actual_expiry_date,
    open_price,
    high_price,
    low_price,
    close_price,
    last_price,
    prev_close_price,
    underlying_price,
    settlement_price,
    open_interest,
    change_in_oi,
    traded_volume,
    lot_size
)
SELECT
    trade_date,
    '1d' AS timeframe,
    instrument_type,
    symbol,
    expiry_date,
    actual_expiry_date,
    open_price,
    high_price,
    low_price,
    close_price,
    last_price,
    prev_close_price,
    underlying_price,
    settlement_price,
    open_interest,
    change_in_oi,
    traded_volume,
    lot_size
FROM fno_bhavcopy_staging
WHERE instrument_type = %s
ON CONFLICT (symbol, timeframe, trade_date, expiry_date)
DO UPDATE SET
    open_price        = EXCLUDED.open_price,
    high_price        = EXCLUDED.high_price,
    low_price         = EXCLUDED.low_price,
    close_price       = EXCLUDED.close_price,
    last_price        = EXCLUDED.last_price,
    prev_close_price  = EXCLUDED.prev_close_price,
    underlying_price  = EXCLUDED.underlying_price,
    settlement_price  = EXCLUDED.settlement_price,
    open_interest     = EXCLUDED.open_interest,
    change_in_oi      = EXCLUDED.change_in_oi,
    traded_volume     = EXCLUDED.traded_volume,
    lot_size          = EXCLUDED.lot_size;
"""

OPTIONS_SQL = """
INSERT INTO {table} (
    trade_date,
    instrument_type,
    symbol,
    expiry_date,
    actual_expiry_date,
    strike_price,
    option_type,
    open_price,
    high_price,
    low_price,
    close_price,
    last_price,
    prev_close_price,
    underlying_price,
    settlement_price,
    open_interest,
    change_in_oi,
    traded_volume,
    lot_size
)
SELECT
    trade_date,
    instrument_type,
    symbol,
    expiry_date,
    actual_expiry_date,
    strike_price,
    option_type,
    open_price,
    high_price,
    low_price,
    close_price,
    last_price,
    prev_close_price,
    underlying_price,
    settlement_price,
    open_interest,
    change_in_oi,
    traded_volume,
    lot_size
FROM fno_bhavcopy_staging
WHERE instrument_type = %s
  AND strike_price IS NOT NULL
  AND option_type IN ('CE','PE')
ON CONFLICT (
    symbol,
    trade_date,
    expiry_date,
    strike_price,
    option_type
) DO UPDATE SET
    open_price        = EXCLUDED.open_price,
    high_price        = EXCLUDED.high_price,
    low_price         = EXCLUDED.low_price,
    close_price       = EXCLUDED.close_price,
    last_price        = EXCLUDED.last_price,
    prev_close_price  = EXCLUDED.prev_close_price,
    underlying_price  = EXCLUDED.underlying_price,
    settlement_price  = EXCLUDED.settlement_price,
    open_interest     = EXCLUDED.open_interest,
    change_in_oi      = EXCLUDED.change_in_oi,
    traded_volume     = EXCLUDED.traded_volume,
    lot_size          = EXCLUDED.lot_size;
"""

# --------------------------------------------------------------------------
def route_staging_to_fno_tables():
    log("🔀 Routing fno_bhavcopy_staging → FNO tables")
    total_rows = 0

    # Use new context-manager based connection
    with get_db_connection_cm() as conn:
        with conn.cursor() as cur:

            try:
                for instrument_code, cfg in FNO_ROUTE_MAP.items():
                    table = cfg["table"]
                    kind = cfg["kind"]

                    log(f"➡️ Processing {instrument_code} → {table}")

                    if kind == "FUT":
                        sql = FUTURES_SQL.format(table=table)
                    elif kind == "OPT":
                        sql = OPTIONS_SQL.format(table=table)
                    else:
                        raise ValueError(f"Unknown instrument kind: {kind}")

                    cur.execute(sql, (instrument_code,))
                    rows = cur.rowcount
                    total_rows += rows

                    log(f"✅ {table}: {rows:,} rows upserted")

                cur.execute("TRUNCATE TABLE fno_bhavcopy_staging;")
                log("🧹 fno_bhavcopy_staging cleared successfully")

                conn.commit()
                log(f"🎉 Routing completed successfully — TOTAL rows upserted: {total_rows:,}")

            except Exception as e:
                conn.rollback()
                log(f"❌ Routing failed — staging NOT cleared: {e}")
                raise

# --------------------------------------------------------------------------