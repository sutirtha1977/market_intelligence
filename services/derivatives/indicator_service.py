import traceback
import time
import sys
import warnings
import pandas as pd
import talib
import numpy as np
from tqdm import tqdm
from database.connection import get_db_connection_cm
from config.logger import log
from config.db_config import FNO_TABLE_MAP

warnings.simplefilter(action="ignore", category=UserWarning)

BATCH_SIZE = 5000

# --------------------------------------------------------------------------
def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    try:
        df = df.sort_values("trade_date").reset_index(drop=True)

        close = np.asarray(df["close_price"], dtype=np.float64)

        # EMA
        df["ema_3"] = talib.EMA(close, 3)
        df["ema_5"] = talib.EMA(close, 5)
        df["ema_7"] = talib.EMA(close, 7)
        df["ema_9"] = talib.EMA(close, 9)
        df["ema_10"] = talib.EMA(close, 10)

        # SMA (ONLY 20 ACTIVE — OTHERS ZERO)
        df["sma_20"] = talib.SMA(close, 20)
        df["sma_50"] = 0
        df["sma_100"] = 0
        df["sma_200"] = 0

        # RSI
        df["rsi_3"] = talib.RSI(close, 3)
        df["rsi_9"] = talib.RSI(close, 9)
        df["rsi_14"] = talib.RSI(close, 14)

        rsi_9 = np.asarray(df["rsi_9"], dtype=np.float64)

        df["ema_rsi_9_3"] = talib.EMA(rsi_9, 3)
        df["ema_rsi_9_5"] = talib.EMA(rsi_9, 5)
        df["wma_rsi_9_21"] = talib.WMA(rsi_9, 21)

        cols = [
            "ema_3","ema_5","ema_7","ema_9","ema_10",
            "sma_20","sma_50","sma_100","sma_200",
            "rsi_3","rsi_9","rsi_14",
            "ema_rsi_9_3","ema_rsi_9_5","wma_rsi_9_21"
        ]

        df[cols] = df[cols].round(2).fillna(0)
        return df

    except Exception as e:
        log(f"{sys._getframe().f_code.co_name} FAILED | {e}")
        traceback.print_exc()
        return df


# --------------------------------------------------------------------------
def refresh_futures_indicators(timeframe: str = "1d") -> None:

    try:
        log("🛠 Started refresh_futures_indicators")

        with get_db_connection_cm() as conn:
            with conn.cursor() as cur:

                # USE FNO_TABLE_MAP ONLY
                futures_map = {
                    "stock": FNO_TABLE_MAP["stock"][1],
                    "index": FNO_TABLE_MAP["index"][1],
                }

                indicators_map = {
                    "stock": FNO_TABLE_MAP["stock"][2],
                    "index": FNO_TABLE_MAP["index"][2],
                }

                for market_type in ["stock", "index"]:

                    table = futures_map[market_type]
                    indicators_table = indicators_map[market_type]

                    log(f"\n📊 Processing: {table} ({market_type})")

                    # --------------------------------------------------
                    # STEP 1: SYMBOL + EXPIRY
                    # --------------------------------------------------
                    cur.execute(f"""
                        SELECT DISTINCT symbol, expiry_date
                        FROM {table}
                        WHERE timeframe = %s
                        ORDER BY symbol, expiry_date
                    """, (timeframe,))

                    symbol_expiries = cur.fetchall()

                    if not symbol_expiries:
                        log(f"⚠️ No data found in {table}")
                        continue

                    total_rows = 0
                    start_time = time.time()

                    # --------------------------------------------------
                    # SYMBOL + EXPIRY LOOP
                    # --------------------------------------------------
                    for symbol, expiry_date in tqdm(
                        symbol_expiries,
                        desc=f"{market_type} contracts",
                        ncols=110
                    ):

                        df = pd.read_sql(f"""
                            SELECT
                                trade_date,
                                expiry_date,
                                open_price,
                                high_price,
                                low_price,
                                close_price
                            FROM {table}
                            WHERE symbol = %s
                              AND expiry_date = %s
                              AND timeframe = %s
                            ORDER BY trade_date
                        """, conn, params=(symbol, expiry_date, timeframe))

                        if df.empty:
                            continue

                        # INDICATORS
                        df_ind = calculate_indicators(df)

                        df_ind.insert(0, "symbol", symbol)
                        df_ind.insert(1, "timeframe", timeframe)

                        insert_sql = f"""
                            INSERT INTO {indicators_table} (
                                symbol, timeframe, trade_date, expiry_date,
                                ema_3, ema_5, ema_7, ema_9, ema_10,
                                sma_20, sma_50, sma_100, sma_200,
                                rsi_3, rsi_9, rsi_14,
                                ema_rsi_9_3, ema_rsi_9_5, wma_rsi_9_21
                            )
                            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                            ON CONFLICT (symbol, timeframe, trade_date, expiry_date)
                            DO UPDATE SET
                                ema_3 = EXCLUDED.ema_3,
                                ema_5 = EXCLUDED.ema_5,
                                ema_7 = EXCLUDED.ema_7,
                                ema_9 = EXCLUDED.ema_9,
                                ema_10 = EXCLUDED.ema_10,
                                sma_20 = EXCLUDED.sma_20,
                                sma_50 = EXCLUDED.sma_50,
                                sma_100 = EXCLUDED.sma_100,
                                sma_200 = EXCLUDED.sma_200,
                                rsi_3 = EXCLUDED.rsi_3,
                                rsi_9 = EXCLUDED.rsi_9,
                                rsi_14 = EXCLUDED.rsi_14,
                                ema_rsi_9_3 = EXCLUDED.ema_rsi_9_3,
                                ema_rsi_9_5 = EXCLUDED.ema_rsi_9_5,
                                wma_rsi_9_21 = EXCLUDED.wma_rsi_9_21
                        """

                        records = list(
                            df_ind[
                                ["symbol","timeframe","trade_date","expiry_date",
                                 "ema_3","ema_5","ema_7","ema_9","ema_10",
                                 "sma_20","sma_50","sma_100","sma_200",
                                 "rsi_3","rsi_9","rsi_14",
                                 "ema_rsi_9_3","ema_rsi_9_5","wma_rsi_9_21"]
                            ].itertuples(index=False, name=None)
                        )

                        for i in range(0, len(records), BATCH_SIZE):
                            cur.executemany(insert_sql, records[i:i+BATCH_SIZE])
                            conn.commit()

                        total_rows += len(records)

                    log(f"✔ {table} ({market_type}) | rows={total_rows} | time={time.time()-start_time:.1f}s")

        log("🎉 All futures indicators updated successfully")

    except Exception as e:
        log(f"❌ FAILED refresh_futures_indicators | {e}")
        traceback.print_exc()
# --------------------------------------------------------------------------