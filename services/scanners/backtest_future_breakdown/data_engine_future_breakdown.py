import pandas as pd

from database.connection import get_engine

TIMEFRAME = "1wk"

# --------------------------------------------------------------------------
def data_logic(selected_year: int) -> pd.DataFrame:

    engine = get_engine()

    query = f"""
    WITH base AS (
        SELECT
            s.symbol,
            i.symbol_id,
            i.timeframe,
            i.date,
            p.high,
            p.low,
            i.rsi_9,
            i.wma_rsi_9_21,
            i.rs,

            LAG(i.rsi_9) OVER (
                PARTITION BY i.symbol_id, i.timeframe
                ORDER BY i.date
            ) AS prev_rsi_9,

            LAG(i.wma_rsi_9_21) OVER (
                PARTITION BY i.symbol_id, i.timeframe
                ORDER BY i.date
            ) AS prev_wma_rsi_9_21

        FROM yahoo_india_equity_symbols s

        JOIN yahoo_india_equity_indicators i
            ON s.symbol_id = i.symbol_id

        JOIN yahoo_india_equity_price p
            ON i.symbol_id = p.symbol_id
            AND i.timeframe = p.timeframe
            AND i.date = p.date

        WHERE
            s.is_future = TRUE
            AND i.timeframe = '{TIMEFRAME}'
            AND EXTRACT(YEAR FROM i.date) = {selected_year}
    )

    SELECT
        date,
        symbol,

        ROUND(
            (
                ((high - low) / NULLIF(low,0)) * 100
            )::numeric,
            2
        ) AS signal_range_pct,

        prev_rsi_9,
        prev_wma_rsi_9_21,
        rsi_9,
        wma_rsi_9_21,
        rs

    FROM base
    ORDER BY date,symbol
    """

    return pd.read_sql(query, engine)