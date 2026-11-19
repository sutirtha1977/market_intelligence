import pandas as pd
from config.db_table import ASSET_TABLE_CONFIG
from database.connection import get_engine

# --------------------------------------------------------------------------
def data_logic(asset_type: str, start_date: str, end_date: str) -> pd.DataFrame:

    tables = ASSET_TABLE_CONFIG[asset_type]
    symbol_table = tables["symbol"]
    price_table = tables["price"]
    indicator_table = tables["indicator"]

    engine = get_engine()

    sql = f"""
    WITH weekly_history AS (
        SELECT
            p.symbol_id,
            s.symbol,
            p.date AS signal_date,

            -- canonical scanner schema (FINAL)
            p.high AS signal_week_high,
            p.low  AS signal_week_low,
            p.adj_close AS signal_week_close,

            i.sma_20,
            i.rsi_3,
            i.rsi_9,
            i.ema_rsi_9_3,
            i.wma_rsi_9_21,
            m.rsi_3 AS rsi_3_monthly

        FROM {price_table} p
        JOIN {indicator_table} i
            ON p.symbol_id = i.symbol_id
            AND p.date = i.date
            AND i.timeframe = '1wk'
        LEFT JOIN LATERAL (
            SELECT mi.rsi_3
            FROM {indicator_table} mi
            WHERE mi.symbol_id = p.symbol_id
              AND mi.timeframe = '1mo'
              AND mi.date <= p.date
            ORDER BY mi.date DESC
            LIMIT 1
        ) m ON TRUE
        JOIN {symbol_table} s
            ON s.symbol_id = p.symbol_id
        WHERE p.timeframe = '1wk'
          AND p.date BETWEEN %(start)s AND %(end)s
          AND i.rs > 0
          AND i.rs > i.rs_ma
    ),

    weekly_with_lookbacks AS (
        SELECT
            wh.*,

            -- previous close
            LAG(wh.signal_week_close, 1)
                OVER (PARTITION BY wh.symbol_id ORDER BY wh.signal_date) AS close_1w_ago,

            -- 2-week SMA reference
            LAG(wh.sma_20, 2)
                OVER (PARTITION BY wh.symbol_id ORDER BY wh.signal_date) AS sma_20_2w_ago,

            -- rolling 4-week low (excluding current week)
            MIN(wh.signal_week_low)
                OVER (
                    PARTITION BY wh.symbol_id
                    ORDER BY wh.signal_date
                    ROWS BETWEEN 4 PRECEDING AND 1 PRECEDING
                ) AS min_low_4w_ago

        FROM weekly_history wh
    )

    SELECT *
    FROM weekly_with_lookbacks
    ORDER BY signal_date, symbol;
    """

    df = pd.read_sql(sql, engine, params={"start": start_date, "end": end_date})

    # safety guard (prevents downstream crashes)
    if df is None or df.empty:
        return pd.DataFrame()

    return df