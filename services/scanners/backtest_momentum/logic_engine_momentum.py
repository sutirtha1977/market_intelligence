import pandas as pd

# --------------------------------------------------------------------------
def apply_scanner_logic(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["daily_signal"] = (
        (df["rsi_3"] / df["rsi_9"] >= 1.15) &
        (df["rsi_9"] / df["ema_rsi_9_3"] < 1.2) &
        (df["ema_rsi_9_3"] >= df["wma_rsi_9_21"]) &
        (df["rsi_3"] < 60) &
        (df["wma_rsi_9_21"].between(30, 50)) &
        (df["rs"] > 0) 
    )

    return df[df["daily_signal"]]
# --------------------------------------------------------------------------