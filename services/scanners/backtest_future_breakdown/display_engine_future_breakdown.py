import pandas as pd

# --------------------------------------------------------------------------
def display_logic(df: pd.DataFrame) -> pd.DataFrame:

    if df.empty:
        return df

    df = df.copy()

    df["date"] = pd.to_datetime(df["date"])

    df.sort_values(
        ["date", "symbol"],
        inplace=True
    )

    df["date"] = (
        df["date"]
        .dt.strftime("%d-%b-%Y")
    )

    df["signal_range_pct"] = (
        df["signal_range_pct"]
        .astype(float)
        .round(2)
    )

    df.rename(
        columns={
            "date": "Date",
            "symbol": "Symbol",
            "signal_range_pct": "Signal Range %"
        },
        inplace=True
    )

    return df[
        [
            "Date",
            "Symbol",
            "Signal Range %"
        ]
    ]