import pandas as pd

from config.india_futures import SYMBOL_START_DATE

# --------------------------------------------------------------------------
def scanner_logic(df: pd.DataFrame) -> pd.DataFrame:

    if df.empty:
        return df

    signals = df[
        (df["prev_rsi_9"] > df["prev_wma_rsi_9_21"])
        & (df["rsi_9"] < df["wma_rsi_9_21"])
        & (df["wma_rsi_9_21"] < df["prev_wma_rsi_9_21"])
        & (df["rs"] < 0)
    ].copy()

    signals["date"] = pd.to_datetime(signals["date"])

    signals["start_date"] = (
        signals["symbol"]
        .map(SYMBOL_START_DATE)
    )

    signals["start_date"] = pd.to_datetime(
        signals["start_date"]
    )

    signals = signals[
        signals["start_date"].notna()
    ]

    signals = signals[
        signals["date"] > signals["start_date"]
    ]

    signals.drop(columns=["start_date"], inplace=True)

    return (
        signals
        .sort_values(["date", "symbol"])
        .reset_index(drop=True)
    )