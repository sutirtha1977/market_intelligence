import os
import pandas as pd

from datetime import timedelta
from typing import Optional

from config.logger import log
from config.db_config import ASSET_TABLE_CONFIG
from database.connection import get_engine


# ==========================================================================
# NEXT MONDAY
# ==========================================================================
def get_next_monday(dt):

    if pd.isna(dt):
        return None

    dt = pd.to_datetime(dt)

    days_ahead = 7 - dt.weekday() if dt.weekday() != 0 else 7

    return dt + timedelta(days=days_ahead)


# ==========================================================================
# BACKTEST LOGIC
# ==========================================================================
def backtest_logic(
    asset_type: str,
    folder_path: Optional[str],
    target_pct: float
) -> pd.DataFrame:

    try:

        # ==================================================================
        # VALIDATION
        # ==================================================================
        if not folder_path:

            log("❌ No folder path provided.")

            return pd.DataFrame()

        folder_path = os.path.abspath(folder_path)

        if not os.path.exists(folder_path):

            log(f"❌ Folder does not exist: {folder_path}")

            return pd.DataFrame()

        # ==================================================================
        # TABLE CONFIG
        # ==================================================================
        tables = ASSET_TABLE_CONFIG.get(asset_type)

        if not tables:

            log(f"❌ Invalid asset_type: {asset_type}")

            return pd.DataFrame()

        price_table = tables["price"]

        symbol_table = price_table.replace(
            "_price",
            "_symbols"
        )

        log(f"📦 PRICE TABLE      : {price_table}")
        log(f"📦 SYMBOL TABLE     : {symbol_table}")

        # ==================================================================
        # CSV FILES
        # ==================================================================
        files = sorted([
            f for f in os.listdir(folder_path)
            if f.endswith(".csv")
        ])

        if not files:

            log("❌ No CSV files found.")

            return pd.DataFrame()

        log(f"📁 CSV FILES FOUND: {len(files)}")

        conn = get_engine()

        summary = []

        # ==================================================================
        # FILE LOOP
        # ==================================================================
        for file in files:

            try:

                log("=" * 100)
                log(f"🚀 PROCESSING FILE: {file}")

                path = os.path.join(folder_path, file)

                # ==========================================================
                # READ CSV
                # ==========================================================
                df = pd.read_csv(path)

                if df is None or df.empty:

                    log(f"⚠️ Empty CSV: {file}")

                    continue

                log(f"📄 CSV Rows: {len(df)}")

                # ==========================================================
                # CLEANING
                # ==========================================================
                df = df.dropna(
                    subset=[
                        "symbol_id",
                        "signal_date",
                        "signal_week_low"
                    ]
                )

                if df.empty:

                    log("⚠️ Data empty after cleaning")

                    continue

                # ----------------------------------------------------------
                # SYMBOL ID
                # ----------------------------------------------------------
                df["symbol_id"] = pd.to_numeric(
                    df["symbol_id"],
                    errors="coerce"
                )

                df = df.dropna(subset=["symbol_id"])

                df["symbol_id"] = df["symbol_id"].astype(int)

                # ----------------------------------------------------------
                # SIGNAL DATE
                # ----------------------------------------------------------
                # df["signal_date"] = pd.to_datetime(
                #     df["signal_date"],
                #     errors="coerce",
                #     dayfirst=True
                # )
                df["signal_date"] = pd.to_datetime(
                    df["signal_date"],
                    format="%Y-%m-%d",
                    errors="coerce"
                )

                df = df.dropna(subset=["signal_date"])

                if df.empty:

                    log("⚠️ No valid signal dates")

                    continue

                # ----------------------------------------------------------
                # SIGNAL WEEK LOW
                # ----------------------------------------------------------
                df["signal_week_low"] = pd.to_numeric(
                    df["signal_week_low"],
                    errors="coerce"
                )

                df = df.dropna(subset=["signal_week_low"])

                if df.empty:

                    log("⚠️ No valid signal week lows")

                    continue

                # ----------------------------------------------------------
                # OUTPUT COLUMN
                # ----------------------------------------------------------
                if "signal_week_low_broke_date" not in df.columns:

                    df["signal_week_low_broke_date"] = ""

                # ==========================================================
                # SYMBOL IDS
                # ==========================================================
                symbol_ids = df["symbol_id"].unique()

                if len(symbol_ids) == 0:

                    log("⚠️ No symbol IDs found")

                    continue

                ids_tuple = tuple(symbol_ids.tolist())

                min_date = df["signal_date"].min()

                max_date = min_date + pd.Timedelta(days=370)

                # ==========================================================
                # FETCH WEEKLY PRICE DATA
                # ==========================================================
                query = f"""
                SELECT

                    p.symbol_id,
                    s.symbol,
                    p.date,
                    p.close

                FROM {price_table} p

                LEFT JOIN {symbol_table} s
                    ON p.symbol_id = s.symbol_id

                WHERE p.symbol_id IN %(ids)s
                  AND p.timeframe = '1wk'
                  AND p.date BETWEEN %(start)s AND %(end)s

                ORDER BY
                    p.symbol_id,
                    p.date
                """

                prices = pd.read_sql(
                    query,
                    conn,
                    params={
                        "ids": ids_tuple,
                        "start": min_date,
                        "end": max_date
                    }
                )

                if prices is None or prices.empty:

                    log("⚠️ No weekly price data fetched")

                    continue

                log(f"📊 Weekly rows fetched: {len(prices)}")

                # ==========================================================
                # CLEAN PRICE DATA
                # ==========================================================
                prices["date"] = pd.to_datetime(
                    prices["date"],
                    errors="coerce"
                )

                prices["close"] = pd.to_numeric(
                    prices["close"],
                    errors="coerce"
                )

                prices = prices.dropna(
                    subset=["date", "close"]
                )

                # ==========================================================
                # PRICE MAP
                # ==========================================================
                price_map = {}

                for sid, grp in prices.groupby("symbol_id"):

                    grp = (
                        grp
                        .sort_values("date")
                        .reset_index(drop=True)
                    )

                    price_map[int(sid)] = grp

                # ==========================================================
                # COUNTERS
                # ==========================================================
                signals = len(df)

                broke_count = 0

                # ==========================================================
                # SIGNAL LOOP
                # ==========================================================
                for idx, row in df.iterrows():

                    try:

                        sid = int(row["symbol_id"])

                        signal_date = row["signal_date"]

                        signal_low = float(
                            row["signal_week_low"]
                        )

                        data = price_map.get(sid)

                        if data is None or data.empty:

                            continue

                        # ==================================================
                        # NEXT WEEK START
                        # ==================================================
                        start = get_next_monday(signal_date)

                        if start is None:

                            continue

                        # ==================================================
                        # YEAR END
                        # ==================================================
                        year_end = pd.Timestamp(
                            year=signal_date.year,
                            month=12,
                            day=31
                        )

                        # ==================================================
                        # FUTURE WEEKLY DATA
                        # ==================================================
                        future = data[
                            (data["date"] >= start) &
                            (data["date"] <= year_end)
                        ].reset_index(drop=True)

                        if future.empty:

                            continue

                        # ==================================================
                        # WEEKLY CLOSE BELOW SIGNAL LOW
                        # ==================================================
                        low_break = future[
                            future["close"] < signal_low
                        ]

                        if not low_break.empty:

                            broke_date = low_break.iloc[0]["date"]

                            df.at[
                                idx,
                                "signal_week_low_broke_date"
                            ] = broke_date.strftime("%Y-%m-%d")

                            broke_count += 1

                    except Exception as e:

                        log(
                            f"🔥 SIGNAL ERROR | "
                            f"File={file} | "
                            f"Symbol={row.get('symbol_id')} | "
                            f"Error={e}"
                        )

                # ==========================================================
                # SAVE UPDATED CSV
                # ==========================================================
                df.to_csv(
                    path,
                    index=False
                )

                log(f"💾 Updated CSV Saved: {path}")

                # ==========================================================
                # LOW BREAK %
                # ==========================================================
                low_break_pct = round(
                    (broke_count / signals) * 100,
                    2
                ) if signals else 0

                # ==========================================================
                # SUMMARY
                # ==========================================================
                summary.append({

                    "File": file,

                    "# of Signals": signals,

                    "# Broke Signal Week Low": broke_count,

                    "% Signal Low Break": low_break_pct
                })

                # ==========================================================
                # LOGGING
                # ==========================================================
                log(
                    f"📊 SUMMARY → "
                    f"Signals={signals} | "
                    f"BrokeLow={broke_count} | "
                    f"Break%={low_break_pct:.2f}"
                )

            except Exception as e:

                log(f"🔥 FILE ERROR: {file} | {e}")

        # ==================================================================
        # FINAL DF
        # ==================================================================
        summary_df = pd.DataFrame(summary)

        if not summary_df.empty:

            # --------------------------------------------------------------
            # EXTRACT YEAR
            # --------------------------------------------------------------
            summary_df["year"] = (
                summary_df["File"]
                .str.extract(r"(\d{4})")[0]
            )

            summary_df["year"] = pd.to_numeric(
                summary_df["year"],
                errors="coerce"
            )

            # --------------------------------------------------------------
            # SORT DESCENDING
            # --------------------------------------------------------------
            summary_df = summary_df.sort_values(
                by=["year", "File"],
                ascending=[False, True]
            )

            # --------------------------------------------------------------
            # CLEANUP
            # --------------------------------------------------------------
            summary_df = (
                summary_df
                .drop(columns=["year"])
                .reset_index(drop=True)
            )

        log("✅ PROCESS COMPLETED")

        return summary_df

    except Exception as e:

        log(f"🔥 ENGINE ERROR: {e}")

        return pd.DataFrame()