from config.db_config import ASSET_TABLE_CONFIG
from database.connection import get_engine
import pandas as pd

def data_logic(asset_type: str, start_date: str, end_date: str):

    tables = ASSET_TABLE_CONFIG[asset_type]
    symbol_table = tables["symbol"]
    price_table = tables["price"]
    indicator_table = tables["indicator"]

    engine = get_engine()

    # ---------------------------------------------------------
    # Dynamic filter based on asset type
    # ---------------------------------------------------------
    price_filter = ""
    if asset_type == "yahoo_india_equity":
        price_filter = "AND p.adj_close >= 100"

    sql = f"""
    WITH base AS (
        SELECT
            d.symbol_id,
            s.symbol,
            d.date AS signal_date,

            -- indicators
            d.rsi_3,
            d.rsi_9,
            d.ema_rsi_9_3,
            d.wma_rsi_9_21,
            d.rs,
            d.rs_ma,
            
            -- price data
            p.high AS signal_week_high,
            p.low  AS signal_week_low,
            p.adj_close AS signal_week_close,

            -- previous values for crossover logic
            LAG(d.rsi_9) OVER (
                PARTITION BY d.symbol_id
                ORDER BY d.date
            ) AS rsi_9_prev,

            LAG(d.wma_rsi_9_21) OVER (
                PARTITION BY d.symbol_id
                ORDER BY d.date
            ) AS wma_prev

        FROM {indicator_table} d

        JOIN {price_table} p
            ON p.symbol_id = d.symbol_id
           AND p.date = d.date
           AND p.timeframe = '1wk'

        JOIN {symbol_table} s
            ON s.symbol_id = d.symbol_id

        WHERE d.timeframe = '1wk'
          AND d.date BETWEEN %(start)s AND %(end)s
          {price_filter}
    )

    SELECT *
    FROM base
    WHERE
        rsi_9_prev IS NOT NULL
        AND wma_prev IS NOT NULL

        AND rsi_9_prev <= wma_prev
        AND rsi_9 > wma_rsi_9_21

        AND wma_rsi_9_21 > wma_prev

        AND rsi_3 > rsi_9

        AND (rsi_9 / NULLIF(ema_rsi_9_3, 0)) < 1.2
        AND rsi_9 > ema_rsi_9_3
        AND ema_rsi_9_3 > wma_rsi_9_21

        AND wma_rsi_9_21 < 50
        
        AND rs > 0
        AND rs > rs_ma


    ORDER BY signal_date DESC;
    """

    return pd.read_sql(
        sql,
        engine,
        params={
            "start": start_date,
            "end": end_date
        }
    )