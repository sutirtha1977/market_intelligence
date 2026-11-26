import os
import pandas as pd
from typing import Optional
from datetime import timedelta

from config.logger import log
from config.db_config import ASSET_TABLE_CONFIG
from database.connection import get_engine

# --------------------------------------------------------------------------
def get_next_monday(dt):
    days_ahead = 7 - dt.weekday() if dt.weekday() != 0 else 7
    return dt + timedelta(days=days_ahead)

# --------------------------------------------------------------------------
def backtest_logic(
    asset_type: str,
    folder_path: Optional[str],
    target_pct: float = 5.0
) -> pd.DataFrame:

    if not folder_path:
        log("❌ No folder path provided.")
        return pd.DataFrame()

    folder_path = os.path.abspath(folder_path)
    
    tables = ASSET_TABLE_CONFIG[asset_type]
    price_table = tables["price"]

    files = sorted(
        [
            f for f in os.listdir(folder_path)
            if os.path.isfile(os.path.join(folder_path, f)) and f.endswith(".csv")
        ]
    )

    if not files:
        log("⚠ No CSV files found")
        return pd.DataFrame()

    engine = get_engine()
    summary = []

    try:
        for file in files:

            path = os.path.join(folder_path, file)
            df = pd.read_csv(path)

            if df.empty:
                log(f"⚠ {file} is empty")
                continue

            # ==========================================================
            # BACKWARD COMPATIBILITY (IMPORTANT)
            # ==========================================================
            if "signal_date" not in df.columns and "date" in df.columns:
                df["signal_date"] = df["date"]

            if "signal_week_high" not in df.columns and "weekly_high" in df.columns:
                df["signal_week_high"] = df["weekly_high"]

            # ---------------- DATE FIX ----------------
            df["signal_date"] = pd.to_datetime(df["signal_date"], errors="coerce")

            if df["signal_date"].isna().any():
                log(f"❌ Date parsing failed in {file}")
                continue

            total_signals = len(df)

            # ---------------- NEXT MONDAY ----------------
            df["start_date"] = df["signal_date"].apply(get_next_monday)

            # ---------------- SYMBOL IDS ----------------
            symbol_ids = df["symbol_id"].astype(int).tolist()

            if not symbol_ids:
                continue

            min_date = df["start_date"].min()
            max_date = min_date + pd.Timedelta(days=370)

            # ---------------- SQL ----------------
            query = f"""
            SELECT symbol_id, date, high, adj_close
            FROM {price_table}
            WHERE symbol_id = ANY(%(ids)s)
            AND timeframe='1d'
            AND date BETWEEN %(start)s AND %(end)s
            ORDER BY symbol_id, date
            """

            params = {
                "ids": symbol_ids,
                "start": min_date.to_pydatetime(),
                "end": max_date.to_pydatetime()
            }

            prices = pd.read_sql(query, engine, params=params)

            if prices.empty:
                log(f"⚠ No price data for {file}")
                continue

            prices["date"] = pd.to_datetime(prices["date"])

            price_map = {
                sid: grp.to_numpy()
                for sid, grp in prices.groupby("symbol_id")
            }

            trades = 0
            wins = 0
            trade_rows = []

            # ==========================================================
            # CORE STRATEGY
            # ==========================================================
            for _, row in df.iterrows():

                sid = int(row["symbol_id"])
                arr = price_map.get(sid)

                if arr is None:
                    continue

                signal_week_high = row["signal_week_high"]
                start_date = row["start_date"]

                entry = None

                for r in arr:
                    if r[1] >= start_date and r[3] > signal_week_high:
                        entry = r
                        break

                if entry is None:
                    continue

                trades += 1
                entry_price = signal_week_high
                target = entry_price * (1 + target_pct / 100)

                future = arr[arr[:, 1] >= entry[1]]

                hit = future[(future[:, 2] >= target) | (future[:, 3] >= target)]

                if len(hit):
                    wins += 1
                    result = "WIN"
                else:
                    result = "NO_TRADE"

                trade_rows.append({
                    "symbol_id": sid,
                    "symbol": row.get("symbol"),
                    "signal_date": row["signal_date"],
                    "entry_date": entry[1],
                    "entry": entry_price,
                    "target": target,
                    "result": result
                })

            win_pct = round((wins / trades) * 100, 2) if trades else 0

            summary.append({
                "File": file,
                "# of Signals": total_signals,
                "# of Trades": trades,
                "# of Wins": wins,
                "% Win": win_pct
            })

            log(
                f"📊 {file} → Signals={total_signals} | Trades={trades} | Wins={wins} | Win%={win_pct}"
            )

        summary_df = pd.DataFrame(summary)

        if not summary_df.empty:
            summary_df["year"] = summary_df["File"].str.extract(r"(\d{4})").astype(int)
            summary_df = summary_df.sort_values("year", ascending=False).reset_index(drop=True)
            summary_df = summary_df.drop(columns=["year"])

        return summary_df

    except Exception as e:
        log(f"❌ Backtest failed | {e}")
        return pd.DataFrame()