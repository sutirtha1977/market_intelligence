import traceback
import warnings
from typing import Optional, List

import pandas as pd
import talib
import numpy as np
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

    df = df.sort_values("date").reset_index(drop=True)

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
    asset_types: Optional[List[str]] = None
) -> None:

    try:
        log("🛠 refresh_indicators started")

        asset_keys = asset_types or ASSET_TABLE_CONFIG.keys()

        # ------------------------------------------------------------------
        # READ ENGINE
        # ------------------------------------------------------------------
        engine = get_engine()

        # ------------------------------------------------------------------
        # WRITE CONNECTION
        # ------------------------------------------------------------------
        with get_db_connection_cm() as write_conn:

            for asset_key in asset_keys:

                tables = ASSET_TABLE_CONFIG[asset_key]

                symbol_table = tables["symbol"]
                price_table = tables["price"]
                indicator_table = tables["indicator"]

                col_id = "symbol_id"

                # ----------------------------------------------------------
                # TRUNCATE TABLE FIRST
                # ----------------------------------------------------------
                log(
                    f"🗑 TRUNCATING {indicator_table}"
                )

                with write_conn.cursor() as cur:

                    cur.execute(
                        f"TRUNCATE TABLE {indicator_table}"
                    )

                write_conn.commit()

                log(
                    f"✅ TRUNCATED {indicator_table}"
                )

                # ----------------------------------------------------------
                asset_ids = pd.read_sql(
                    f"""
                    SELECT {col_id}
                    FROM {symbol_table}
                    """,
                    engine
                )[col_id].tolist()

                for timeframe in FREQUENCIES:

                    log(
                        f"✅ UPDATING {indicator_table} "
                        f"| TIMEFRAME={timeframe}"
                    )

                    for asset_id in tqdm(
                        asset_ids,
                        ncols=100,
                        desc=timeframe
                    ):

                        df = pd.read_sql(
                            f"""
                            SELECT
                                date,
                                open,
                                high,
                                low,
                                close,
                                adj_close,
                                volume
                            FROM {price_table}
                            WHERE {col_id}=%s
                              AND timeframe=%s
                            ORDER BY date
                            """,
                            engine,
                            params=(
                                asset_id,
                                timeframe
                            )
                        )

                        if df.empty:
                            continue

                        ind = calculate_indicators(df)

                        if ind.empty:
                            continue

                        ind.insert(
                            0,
                            col_id,
                            asset_id
                        )

                        ind.insert(
                            1,
                            "timeframe",
                            timeframe
                        )

                        columns = list(ind.columns)

                        column_sql = ",".join(columns)

                        placeholders = ",".join(
                            ["%s"] * len(columns)
                        )

                        # --------------------------------------------------
                        # INSERT ONLY
                        # --------------------------------------------------
                        insert_sql = f"""
                        INSERT INTO {indicator_table}
                        ({column_sql})
                        VALUES ({placeholders})
                        """

                        rows = list(
                            ind.itertuples(
                                index=False,
                                name=None
                            )
                        )

                        with write_conn.cursor() as cur:

                            cur.executemany(
                                insert_sql,
                                rows
                            )

                write_conn.commit()

                log(
                    f"✅ COMPLETED {indicator_table}"
                )

        log(
            "✅ INDICATORS REBUILT SUCCESSFULLY"
        )

    except Exception as e:

        log(
            f"❌ REFRESH_INDICATORS FAILED | {e}"
        )

        traceback.print_exc()
# --------------------------------------------------------------------------