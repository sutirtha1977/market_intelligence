from typing import Callable, Optional

import pandas as pd
import numpy as np
from tqdm import tqdm
from sqlalchemy import text

from database.connection import get_engine, get_db_connection_cm
from config.logger import log
from config.db_config import ASSET_TABLE_CONFIG
from config.constants import FREQUENCIES


# ==========================================================================
# CONFIG
# ==========================================================================
# Pine default:
# length = 123
LOOKBACK = 123

# Pine:
# lengthRSMA = 50
RS_MA_LEN = 50

# Pine:
# ta.rising(..., 3)
TREND_BARS = 3

# Pine:
# base = 5
RS_SLOPE_PERIOD = 5

BATCH_SIZE = 5000


# ==========================================================================
# GET INDEX ID
# ==========================================================================
def get_index_id(engine, symbol_table):

    query = text(f"""
        SELECT symbol_id
        FROM {symbol_table}
        WHERE name ILIKE '%Nifty%'
        LIMIT 1
    """)

    with engine.connect() as conn:
        df = pd.read_sql(query, conn)

    if df.empty:
        raise Exception("❌ Index not found")

    return int(df.iloc[0]["symbol_id"])


# ==========================================================================
# PINE RS FORMULA
#
# Pine:
# res = base/base[length] /
#       (index/index[length]) - 1
# ==========================================================================
def compute_rs_series(stock, index, length):

    stock = pd.Series(stock, dtype="float64")
    index = pd.Series(index, dtype="float64")

    rs = (
        (stock / stock.shift(length)) /
        (index / index.shift(length))
    ) - 1

    return rs


# ==========================================================================
# EXACT PINE ta.rising(x, bars)
#
# ta.rising(x, 3):
#
# x     > x[1]
# x[1]  > x[2]
# x[2]  > x[3]
# ==========================================================================
def ta_rising(series, bars=3):

    result = pd.Series(True, index=series.index)

    for i in range(bars):

        result &= (
            series.shift(i) >
            series.shift(i + 1)
        )

    return result


# ==========================================================================
# EXACT PINE ta.falling(x, bars)
# ==========================================================================
def ta_falling(series, bars=3):

    result = pd.Series(True, index=series.index)

    for i in range(bars):

        result &= (
            series.shift(i) <
            series.shift(i + 1)
        )

    return result


# ==========================================================================
# MAIN ENGINE
# ==========================================================================
def run_rs_engine(
    asset_type,
    progress_callback: Optional[Callable[[str, str, int, int], None]] = None,
):

    engine = get_engine()

    cfg = ASSET_TABLE_CONFIG[asset_type]

    # ----------------------------------------------------------------------
    # INDEX MAPPING
    # ----------------------------------------------------------------------
    INDEX_MAPPING = {
        "yahoo_india_equity": "yahoo_india_index",
        "nse_india_index": "yahoo_india_index",
        "yahoo_india_index": "nse_india_index",
    }

    index_asset_type = INDEX_MAPPING.get(asset_type)

    if not index_asset_type:
        raise Exception(
            f"❌ No index mapping defined for {asset_type}"
        )

    index_cfg = ASSET_TABLE_CONFIG[index_asset_type]
    
    PRICE = cfg["price"]
    INDICATORS = cfg["indicator"]

    INDEX_PRICE = index_cfg["price"]

    nifty_id = get_index_id(
        engine,
        index_cfg["symbol"]
    )

    # ======================================================================
    # TIMEFRAME LOOP
    # ======================================================================
    for timeframe in FREQUENCIES:

        log(
            f"🚀 Computing RS for "
            f"{asset_type} | {timeframe}"
        )

        try:

            # ------------------------------------------------------------------
            # STOCK DATA
            # ------------------------------------------------------------------
            stock_query = text(f"""
                SELECT
                    symbol_id,
                    date,
                    COALESCE(adj_close, close) AS stock_close
                FROM {PRICE}
                WHERE timeframe = :timeframe
                ORDER BY symbol_id, date
            """)

            # ------------------------------------------------------------------
            # INDEX DATA
            # ------------------------------------------------------------------
            index_query = text(f"""
                SELECT
                    date,
                    COALESCE(adj_close, close) AS index_close
                FROM {INDEX_PRICE}
                WHERE symbol_id = :nifty_id
                  AND timeframe = :timeframe
                ORDER BY date
            """)

            with engine.connect() as conn:

                stock_df = pd.read_sql(
                    stock_query,
                    conn,
                    params={
                        "timeframe": timeframe
                    }
                )

                index_df = pd.read_sql(
                    index_query,
                    conn,
                    params={
                        "nifty_id": nifty_id,
                        "timeframe": timeframe
                    }
                )

            # ------------------------------------------------------------------
            # CLEAN INDEX
            # ------------------------------------------------------------------
            index_df = (
                index_df
                .sort_values("date")
                .drop_duplicates("date")
            )

            results = []

            # ==================================================================
            # SYMBOL LOOP
            # ==================================================================
            total_symbols = stock_df["symbol_id"].nunique()
            completed_symbols = 0

            def report_progress(phase: str, completed: int, total: int) -> None:
                if progress_callback:
                    progress_callback(timeframe, phase, completed, total)

            if progress_callback:
                report_progress("Computing RS", 0, total_symbols)

            for symbol_id, g in stock_df.groupby(
                "symbol_id",
                sort=False
            ):

                g = (
                    g
                    .sort_values("date")
                    .drop_duplicates("date")
                )

                # --------------------------------------------------------------
                # EXACT TV STYLE ALIGNMENT
                #
                # TradingView aligns bars naturally.
                # Use INNER JOIN.
                # --------------------------------------------------------------
                merged = g.merge(
                    index_df,
                    on="date",
                    how="inner"
                )

                if merged.empty:
                    completed_symbols += 1
                    report_progress("Computing RS", completed_symbols, total_symbols)
                    continue

                # --------------------------------------------------------------
                # REMOVE INVALID
                # --------------------------------------------------------------
                merged = merged.dropna(
                    subset=[
                        "stock_close",
                        "index_close"
                    ]
                )

                if merged.empty:
                    completed_symbols += 1
                    report_progress("Computing RS", completed_symbols, total_symbols)
                    continue

                # --------------------------------------------------------------
                # NEED ENOUGH HISTORY
                # --------------------------------------------------------------
                min_bars_needed = (
                    LOOKBACK +
                    RS_MA_LEN +
                    TREND_BARS +
                    RS_SLOPE_PERIOD
                )

                if len(merged) < min_bars_needed:
                    completed_symbols += 1
                    report_progress("Computing RS", completed_symbols, total_symbols)
                    continue

                # ==============================================================
                # RS
                # Pine:
                #
                # res = base/base[length] /
                #       (index/index[length]) - 1
                # ==============================================================
                merged["rs"] = compute_rs_series(
                    merged["stock_close"],
                    merged["index_close"],
                    LOOKBACK
                )

                # ==============================================================
                # RS SMA
                #
                # Pine:
                # sma_res = ta.sma(res, lengthRSMA)
                # ==============================================================
                merged["rs_ma"] = (
                    merged["rs"]
                    .rolling(
                        window=RS_MA_LEN,
                        min_periods=RS_MA_LEN
                    )
                    .mean()
                )

                # ==============================================================
                # PINE RS TREND
                #
                # Pine:
                #
                # y0 = res - res[base]
                # angle0 = math.atan(y0 / base)
                # ==============================================================
                merged["rs_slope"] = np.arctan(
                    (
                        merged["rs"] -
                        merged["rs"].shift(
                            RS_SLOPE_PERIOD
                        )
                    ) / RS_SLOPE_PERIOD
                )

                # ==============================================================
                # PINE ta.rising(sma_res, 3)
                # ==============================================================
                merged["rs_ma_rising"] = ta_rising(
                    merged["rs_ma"],
                    TREND_BARS
                )

                # ==============================================================
                # PINE ta.falling(sma_res, 3)
                # ==============================================================
                merged["rs_ma_falling"] = ta_falling(
                    merged["rs_ma"],
                    TREND_BARS
                )

                # --------------------------------------------------------------
                # REMOVE EARLY NAN REGION
                # --------------------------------------------------------------
                merged = merged.dropna(
                    subset=[
                        "rs",
                        "rs_ma",
                        "rs_slope"
                    ]
                ).copy()

                if merged.empty:
                    completed_symbols += 1
                    report_progress("Computing RS", completed_symbols, total_symbols)
                    continue

                # --------------------------------------------------------------
                # FINAL COLUMNS
                # --------------------------------------------------------------
                results.append(
                    merged[[
                        "symbol_id",
                        "date",

                        "rs",
                        "rs_ma",
                        "rs_slope",

                        "rs_ma_rising",
                        "rs_ma_falling"
                    ]]
                )
                completed_symbols += 1
                report_progress("Computing RS", completed_symbols, total_symbols)

            # ==================================================================
            # FINAL DF
            # ==================================================================
            if not results:

                log(
                    f"❌ No RS generated "
                    f"[{timeframe}]"
                )
                if total_symbols == 0:
                    report_progress("Computing RS", 1, 1)

                continue

            final_df = pd.concat(
                results,
                ignore_index=True
            )

            # ------------------------------------------------------------------
            # CLEAN
            # ------------------------------------------------------------------
            final_df = final_df.replace(
                [np.inf, -np.inf],
                np.nan
            )

            final_df = final_df.dropna(
                subset=[
                    "rs",
                    "rs_ma"
                ]
            )

            log(
                f"📊 FINAL ROWS "
                f"[{timeframe}]: {len(final_df)}"
            )

            # ==================================================================
            # UPSERT
            # ==================================================================
            with get_db_connection_cm() as conn:

                cur = conn.cursor()

                data = [
                    (
                        int(r.symbol_id),

                        timeframe,

                        r.date,

                        float(r.rs)
                        if pd.notna(r.rs)
                        else None,

                        float(r.rs_ma)
                        if pd.notna(r.rs_ma)
                        else None,

                        float(r.rs_slope)
                        if pd.notna(r.rs_slope)
                        else None,

                        bool(r.rs_ma_rising)
                        if pd.notna(r.rs_ma_rising)
                        else None,

                        bool(r.rs_ma_falling)
                        if pd.notna(r.rs_ma_falling)
                        else None
                    )
                    for r in final_df.itertuples()
                ]

                # --------------------------------------------------------------
                # BATCH UPSERT
                # --------------------------------------------------------------
                total_batches = (len(data) + BATCH_SIZE - 1) // BATCH_SIZE
                report_progress("Saving RS", 0, total_batches)

                for completed_batches, i in enumerate(tqdm(
                    range(0, len(data), BATCH_SIZE),
                    disable=progress_callback is not None,
                ), start=1):

                    cur.executemany(f"""
                        INSERT INTO {INDICATORS} (

                            symbol_id,
                            timeframe,
                            date,

                            rs,
                            rs_ma,
                            rs_slope,

                            rs_ma_rising,
                            rs_ma_falling

                        )
                        VALUES (
                            %s,%s,%s,
                            %s,%s,%s,
                            %s,%s
                        )

                        ON CONFLICT (
                            symbol_id,
                            timeframe,
                            date
                        )

                        DO UPDATE SET

                            rs = EXCLUDED.rs,
                            rs_ma = EXCLUDED.rs_ma,
                            rs_slope = EXCLUDED.rs_slope,

                            rs_ma_rising =
                                EXCLUDED.rs_ma_rising,

                            rs_ma_falling =
                                EXCLUDED.rs_ma_falling

                    """, data[i:i + BATCH_SIZE])
                    report_progress("Saving RS", completed_batches, total_batches)

                conn.commit()

            log(
                f"✅ DONE "
                f"{asset_type} [{timeframe}]"
            )

        except Exception as e:

            log(
                f"🔥 FAILED "
                f"{asset_type} [{timeframe}] : {e}"
            )