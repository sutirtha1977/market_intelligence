import pandas as pd

def scanner_logic(df: pd.DataFrame, asset_type: str) -> pd.DataFrame:
    if df.empty:
        return df

    df = df.dropna(subset=[
        "close_1w_ago",
        "sma_20_2w_ago",
        "min_low_4w_ago",
        "ema_rsi_9_3",
        "wma_rsi_9_21"
    ])

    # -------------------------------------------------
    # CONDITIONAL FILTER BASED ON ASSET TYPE
    # -------------------------------------------------
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

    # only for India equity
    if asset_type == "yahoo_india_equity":
        base_filter = base_filter & (df["signal_week_close"] >= 100)

    signals = df[base_filter]

    return signals.sort_values(["signal_date", "symbol"]).reset_index(drop=True)

# --------------------------------------------------------------------------