import pandas as pd

# --------------------------------------------------------------------------
def display_logic(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df

    df = df.copy()

    # ==========================================================
    # DATE HANDLING (UPDATED COLUMN)
    # ==========================================================
    df["signal_date"] = pd.to_datetime(df["signal_date"])
    df["signal_date_dt"] = df["signal_date"]

    df.sort_values("signal_date_dt", ascending=False, inplace=True)

    df["signal_date"] = df["signal_date_dt"].dt.strftime("%d-%b-%Y")
    df.drop(columns=["signal_date_dt"], inplace=True)

    # ==========================================================
    # CLEAN SYMBOL
    # ==========================================================
    df["symbol"] = df["symbol"].str.replace(r"\.NS$", "", regex=True)

    # ==========================================================
    # NUMERIC COLUMNS (UPDATED SCHEMA)
    # ==========================================================
    num_cols = [
        "signal_week_high",
        "signal_week_low",
        "signal_week_close",
        "sma_20",
        "rsi_3",
        "rsi_9",
        "ema_rsi_9_3",
        "wma_rsi_9_21",
        "rsi_3_monthly",
        "close_1w_ago",
        "sma_20_2w_ago",
        "min_low_4w_ago"
    ]

    # safe conversion
    for col in num_cols:
        if col in df.columns:
            df[col] = df[col].astype(float).round(2).astype(str)

    # ==========================================================
    # RENAME MAP (UPDATED)
    # ==========================================================
    rename_map = {
        "symbol_id": "ID",
        "symbol": "Symbol",
        "signal_date": "Date",
        "signal_week_high": "Week High",
        "signal_week_low": "Week Low",
        "signal_week_close": "Week Close",
        "sma_20": "SMA 20",
        "rsi_3": "RSI 3",
        "rsi_9": "RSI 9",
        "ema_rsi_9_3": "EMA RSI",
        "wma_rsi_9_21": "WMA RSI",
        "rsi_3_monthly": "Monthly RSI",
        "close_1w_ago": "Prev Week Close",
        "sma_20_2w_ago": "SMA 20 (2W Ago)",
        "min_low_4w_ago": "4W Low"
    }

    df.rename(columns=rename_map, inplace=True)

    # ==========================================================
    # COLUMN ORDER (CLEAN UI OUTPUT)
    # ==========================================================
    preferred_order = [
        "ID",
        "Symbol",
        "Date",
        "Week High",
        "Week Low",
        "Week Close",
        "SMA 20",
        "RSI 3",
        "RSI 9",
        "EMA RSI",
        "WMA RSI",
        "Monthly RSI",
        "Prev Week Close",
        "SMA 20 (2W Ago)",
        "4W Low"
    ]

    cols = [c for c in preferred_order if c in df.columns] + [
        c for c in df.columns if c not in preferred_order
    ]

    return df[cols]