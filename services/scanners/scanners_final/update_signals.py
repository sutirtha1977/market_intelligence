import pandas as pd
import traceback

from database.connection import get_db_connection_cm
from config.db_table import ASSET_TABLE_CONFIG
from config.logger import log

# --------------------------------------------------------------------------
def get_scanner_table(scanner_table_map = "signals"):
    table = ASSET_TABLE_CONFIG["scanner"].get(scanner_table_map)
    if not table:
        raise ValueError(f"Invalid scanner table map: {scanner_table_map}")
    return table

# --------------------------------------------------------------------------
def fetch_latest_closes(symbol_ids, price_table, cur):
    """
    Fetch latest adj_close per symbol (robust & deterministic)
    """
    if not symbol_ids:
        return {}

    cur.execute(f"""
        SELECT symbol_id, adj_close
        FROM (
            SELECT
                symbol_id,
                adj_close,
                ROW_NUMBER() OVER (
                    PARTITION BY symbol_id
                    ORDER BY date DESC
                ) as rn
            FROM {price_table}
            WHERE symbol_id = ANY(%s)
              AND timeframe = '1d'
        ) t
        WHERE rn = 1;
    """, (symbol_ids,))

    result = dict(cur.fetchall())

    log(f"Fetched latest prices: {len(result)} / {len(symbol_ids)}", level="DEBUG")

    return result

# --------------------------------------------------------------------------
def upsert_scanner_signals(
    df: pd.DataFrame,
    asset_type: str,
    scanner_type: str,
    scanner_freq: str = "1wk"
):

    if df.empty:
        log(
            f"No signals to upsert | {asset_type} | {scanner_type} | {scanner_freq}",
            level="INFO"
        )
        return

    try:
        from psycopg2.extras import execute_values

        df = df.copy()

        log(
            f"Upsert start | {asset_type} | {scanner_type} | {scanner_freq} | rows={len(df)}",
            level="DEBUG"
        )

        required_cols = [
            "symbol_id",
            "signal_date",
            "signal_week_high",
            "signal_week_close",
            "rsi_3",
            "rsi_9",
            "ema_rsi_9_3",
            "wma_rsi_9_21"
        ]

        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            raise ValueError(f"Missing columns: {missing}")

        df = df.drop_duplicates(subset=["symbol_id", "signal_date"])

        scanner_table = get_scanner_table()

        with get_db_connection_cm() as conn:
            with conn.cursor() as cur:

                tables = ASSET_TABLE_CONFIG.get(asset_type)
                if not tables:
                    raise ValueError(f"Invalid asset_type: {asset_type}")

                price_table = tables["price"]

                symbol_ids = df["symbol_id"].unique().tolist()
                latest_close_map = fetch_latest_closes(symbol_ids, price_table, cur)

                df["current_close"] = df["symbol_id"].map(latest_close_map)

                missing_symbols = (
                    df[df["current_close"].isna()]["symbol_id"]
                    .unique()
                )

                if len(missing_symbols) > 0:
                    log(
                        f"Missing prices for symbols: {missing_symbols[:10]}",
                        level="WARNING"
                    )

                df["current_close"] = df["current_close"].fillna(0)

                records = list(
                    df[
                        [
                            "symbol_id",
                            "signal_date",
                            "signal_week_high",
                            "signal_week_close",
                            "current_close",
                            "rsi_3",
                            "rsi_9",
                            "ema_rsi_9_3",
                            "wma_rsi_9_21"
                        ]
                    ].itertuples(index=False, name=None)
                )

                execute_values(
                    cur,
                    f"""
                    INSERT INTO {scanner_table} (
                        asset_type,
                        scanner_type,
                        scanner_freq,
                        symbol_id,
                        signal_date,
                        breakout_high,
                        breakout_close,
                        current_close,
                        rsi_3,
                        rsi_9,
                        ema_rsi_9_3,
                        wma_rsi_9_21
                    )
                    VALUES %s
                    ON CONFLICT (
                        asset_type,
                        scanner_type,
                        scanner_freq,
                        symbol_id,
                        signal_date
                    )
                    DO UPDATE SET
                        breakout_high = EXCLUDED.breakout_high,
                        breakout_close = EXCLUDED.breakout_close,
                        current_close = EXCLUDED.current_close,
                        rsi_3 = EXCLUDED.rsi_3,
                        rsi_9 = EXCLUDED.rsi_9,
                        ema_rsi_9_3 = EXCLUDED.ema_rsi_9_3,
                        wma_rsi_9_21 = EXCLUDED.wma_rsi_9_21;
                    """,
                    [
                        (
                            asset_type,
                            scanner_type,
                            scanner_freq,
                            r[0],  # symbol_id
                            r[1],  # signal_date
                            r[2],  # breakout_high
                            r[3],  # breakout_close
                            r[4],  # current_close
                            r[5],  # rsi_3
                            r[6],  # rsi_9
                            r[7],  # ema_rsi_9_3
                            r[8],  # wma_rsi_9_21
                        )
                        for r in records
                    ],
                    page_size=1000
                )

        log(f"Upsert success | rows={len(records)}", level="INFO")

    except Exception as e:
        log(f"Upsert failed | error={e}", level="ERROR")
        log(traceback.format_exc(), level="ERROR")

# --------------------------------------------------------------------------
def update_trigger_flags(asset_type: str, scanner_type: str):

    try:
        log(f"Trigger update start | {asset_type} | {scanner_type}", level="DEBUG")

        scanner_table = get_scanner_table()

        tables = ASSET_TABLE_CONFIG.get(asset_type)
        if not tables:
            raise ValueError(f"Invalid asset_type: {asset_type}")

        price_table = tables["price"]

        with get_db_connection_cm() as conn:
            with conn.cursor() as cur:

                cur.execute(f"""
                    UPDATE {scanner_table} s
                    SET 
                        is_triggered = TRUE,
                        trigger_date = t.trigger_date
                    FROM (
                        SELECT
                            s.symbol_id,
                            s.signal_date,
                            MIN(p.date) AS trigger_date
                        FROM {scanner_table} s
                        JOIN {price_table} p
                            ON p.symbol_id = s.symbol_id
                            AND p.timeframe = '1d'
                            AND p.date > s.signal_date
                            AND p.adj_close > s.breakout_high
                        WHERE s.is_triggered = FALSE
                          AND s.asset_type = %s
                          AND s.scanner_type = %s
                        GROUP BY s.symbol_id, s.signal_date
                    ) t
                    WHERE s.symbol_id = t.symbol_id
                      AND s.signal_date = t.signal_date
                      AND s.asset_type = %s
                      AND s.scanner_type = %s;
                """, (asset_type, scanner_type, asset_type, scanner_type))

                log(f"Trigger rows updated: {cur.rowcount}", level="DEBUG")

        log(f"Trigger update success | {asset_type} | {scanner_type}", level="INFO")

    except Exception as e:
        log(f"Trigger update failed | error={e}", level="ERROR")
        log(traceback.format_exc(), level="ERROR")
# --------------------------------------------------------------------------