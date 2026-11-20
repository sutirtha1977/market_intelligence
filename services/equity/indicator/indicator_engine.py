import traceback
import warnings
from typing import Callable, List, Optional

import pandas as pd
import talib
import numpy as np
from psycopg2.extras import execute_values
from tqdm import tqdm

from database.connection import (
    get_engine,
    get_db_connection_cm
)

from config.constants import FREQUENCIES
from config.db_config import ASSET_TABLE_CONFIG
from services.equity.validation_service import validate_dataframe_columns
from config.logger import log

# --------------------------------------------------------------------------
warnings.simplefilter(action="ignore", category=UserWarning)
SYMBOL_BATCH_SIZE = 50
# --------------------------------------------------------------------------
def calculate_indicators(
    df: pd.DataFrame,
    asset_id: Optional[int] = None,
    timeframe: Optional[str] = None
) -> pd.DataFrame:

    validate_dataframe_columns(
        df,
        [
            "date",
            "open",
            "high",
            "low",
            "close",
            "adj_close",
            "volume"
        ],
        context="Calculate indicators",
    )

    if not df["date"].is_monotonic_increasing:
        df = df.sort_values("date")
    df = df.reset_index(drop=True)

    price = np.where(
        df["adj_close"] > 0,
        df["adj_close"],
        df["close"]
    ).astype(np.float64)

    volume = df["volume"].to_numpy(dtype=np.float64)

    out = pd.DataFrame()

    out["date"] = df["date"]

    out["ema_3"] = talib.EMA(price, 3)
    out["ema_5"] = talib.EMA(price, 5)
    out["ema_7"] = talib.EMA(price, 7)
    out["ema_9"] = talib.EMA(price, 9)
    out["ema_10"] = talib.EMA(price, 10)

    out["sma_20"] = talib.SMA(price, 20)
    out["sma_50"] = talib.SMA(price, 50)
    out["sma_100"] = talib.SMA(price, 100)
    out["sma_200"] = talib.SMA(price, 200)

    out["sma_10_vol"] = talib.SMA(volume, 10)
    out["sma_20_vol"] = talib.SMA(volume, 20)

    out["rsi_3"] = talib.RSI(price, 3)
    out["rsi_9"] = talib.RSI(price, 9)
    out["rsi_14"] = talib.RSI(price, 14)

    # --------------------------------------------------
    # NEW: RSI(10) ON EMA(21)
    # --------------------------------------------------
    ema_21_price = talib.EMA(price, 21)

    out["rsi_10_ema_21"] = talib.RSI(
        ema_21_price,
        timeperiod=10
    )

    rsi9 = out["rsi_9"].to_numpy(dtype=np.float64)

    out["ema_rsi_9_3"] = talib.EMA(rsi9, 3)
    out["ema_rsi_9_5"] = talib.EMA(rsi9, 5)
    out["wma_rsi_9_21"] = talib.WMA(rsi9, 21)

    macd, macd_signal, _ = talib.MACD(
        price,
        fastperiod=12,
        slowperiod=26,
        signalperiod=9
    )

    out["macd"] = macd
    out["macd_signal"] = macd_signal

    bb_u, bb_m, bb_l = talib.BBANDS(
        price,
        timeperiod=20,
        nbdevup=2,
        nbdevdn=2
    )

    out["bb_upper"] = bb_u
    out["bb_middle"] = bb_m
    out["bb_lower"] = bb_l

    return out.round(2).fillna(0)

# --------------------------------------------------------------------------
def refresh_indicators(
    asset_types: Optional[List[str]] = None,
    progress_callback: Optional[Callable[[str, int, int], None]] = None,
) -> None:

    try:
        log("🛠 refresh_indicators started")

        asset_keys = asset_types or [
            key
            for key, tables in ASSET_TABLE_CONFIG.items()
            if all(column in tables for column in ("symbol", "price", "indicator"))
        ]
        engine = get_engine()

        with get_db_connection_cm() as write_conn:
            for asset_key in asset_keys:
                tables = ASSET_TABLE_CONFIG[asset_key]
                symbol_table = tables["symbol"]
                price_table = tables["price"]
                indicator_table = tables["indicator"]
                log(f"🗑 TRUNCATING {indicator_table}")
                with write_conn.cursor() as cur:
                    cur.execute(f"TRUNCATE TABLE {indicator_table}")

                asset_ids = pd.read_sql(
                    f"""
                    SELECT symbol_id
                    FROM {symbol_table}
                    """,
                    engine
                )["symbol_id"].tolist()
                total_assets = len(asset_ids)
                insert_sql = None

                for timeframe in FREQUENCIES:
                    log(f"✅ UPDATING {indicator_table} | TIMEFRAME={timeframe}")
                    if progress_callback:
                        progress_callback(timeframe, 0, total_assets)

                    terminal_progress = (
                        None
                        if progress_callback
                        else tqdm(total=total_assets, ncols=100, desc=timeframe)
                    )
                    completed_assets = 0
                    try:
                        for start in range(0, total_assets, SYMBOL_BATCH_SIZE):
                            asset_batch = asset_ids[start:start + SYMBOL_BATCH_SIZE]
                            placeholders = ",".join(["%s"] * len(asset_batch))
                            price_rows = pd.read_sql(
                                f"""
                                SELECT
                                    symbol_id,
                                    date,
                                    open,
                                    high,
                                    low,
                                    close,
                                    adj_close,
                                    volume
                                FROM {price_table}
                                WHERE symbol_id IN ({placeholders})
                                  AND timeframe=%s
                                ORDER BY symbol_id, date
                                """,
                                engine,
                                params=(*asset_batch, timeframe),
                            )
                            asset_data = {
                                symbol_id: rows.drop(columns="symbol_id")
                                for symbol_id, rows in price_rows.groupby(
                                    "symbol_id",
                                    sort=False
                                )
                            }

                            for asset_id in asset_batch:
                                symbol_data = asset_data.get(asset_id)
                                if symbol_data is not None and not symbol_data.empty:
                                    indicators = calculate_indicators(symbol_data)
                                    if not indicators.empty:
                                        if insert_sql is None:
                                            columns = [
                                                "symbol_id",
                                                "timeframe",
                                                *indicators.columns,
                                            ]
                                            insert_sql = f"""
                                                INSERT INTO {indicator_table}
                                                ({",".join(columns)})
                                                VALUES %s
                                            """

                                        rows = [
                                            (asset_id, timeframe, *values)
                                            for values in indicators.itertuples(
                                                index=False,
                                                name=None
                                            )
                                        ]
                                        with write_conn.cursor() as cur:
                                            execute_values(
                                                cur,
                                                insert_sql,
                                                rows,
                                                page_size=1000,
                                            )

                                completed_assets += 1
                                if terminal_progress is not None:
                                    terminal_progress.update(1)
                                if progress_callback:
                                    progress_callback(
                                        timeframe,
                                        completed_assets,
                                        total_assets,
                                    )
                    finally:
                        if terminal_progress is not None:
                            terminal_progress.close()

                write_conn.commit()
                log(f"✅ COMPLETED {indicator_table}")

        log("✅ INDICATORS REBUILT SUCCESSFULLY")

    except Exception:
        log(f"❌ REFRESH_INDICATORS FAILED\n{traceback.format_exc()}")
        raise
# --------------------------------------------------------------------------