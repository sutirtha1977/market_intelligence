
# services/scanners/scanner_weekly/logic_engine_weekly.py

import pandas as pd


def scanner_logic(
    df: pd.DataFrame,
    asset_type: str
) -> pd.DataFrame:

    if df is None or df.empty:
        return pd.DataFrame()

    required_columns = [
        "close_1w_ago",
        "sma_20_2w_ago",
        "min_low_4w_ago",
        "ema_rsi_9_3",
        "wma_rsi_9_21"
    ]

    df = df.dropna(subset=required_columns)

    # --------------------------------------------------
    # WEEKLY SCANNER CONDITIONS
    # --------------------------------------------------
    base_filter = (
        (df["signal_week_close"] > df["sma_20"]) &
        (df["signal_week_low"] <= df["min_low_4w_ago"]) &
        (df["sma_20_2w_ago"] < df["sma_20"]) &
        (df["signal_week_close"] >= df["close_1w_ago"]) &
        (df["rsi_3"] > df["rsi_9"]) &
        (df["rsi_9"] > df["ema_rsi_9_3"]) &
        (df["ema_rsi_9_3"] > df["wma_rsi_9_21"]) &
        (df["rsi_3"] > 50) &
        (df["rsi_3_monthly"] > 50)
    )

    # India equity price filter
    if asset_type == "yahoo_india_equity":
        base_filter &= df["signal_week_close"] >= 100

    return (
        df.loc[base_filter]
        .sort_values(
            ["signal_date", "symbol"]
        )
        .reset_index(drop=True)
    )
