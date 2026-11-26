import pandas as pd

# --------------------------------------------------------------------------
def display_logic(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df

    df = df.copy()

    # ==========================================================
    # DATE HANDLING
    # ==========================================================
    if "signal_date" in df.columns:
        df["signal_date"] = pd.to_datetime(df["signal_date"], errors="coerce")
        df = df.sort_values("signal_date", ascending=False)
        df["signal_date"] = df["signal_date"].dt.strftime("%d-%b-%Y")

    # ==========================================================
    # CLEAN SYMBOL
    # ==========================================================
    if "symbol" in df.columns:
        df["symbol"] = df["symbol"].astype(str).str.replace(r"\.NS$", "", regex=True)

    # ==========================================================
    # NUMERIC FORMATTING (ONLY EXISTING COLS)
    # ==========================================================
    num_cols = [
        "signal_week_high",
        "signal_week_low",
        "signal_week_close",
        "rsi_3",
        "rsi_9",
        "ema_rsi_9_3",
        "wma_rsi_9_21",
        "rsi_9_prev",
        "wma_prev"
    ]

    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").round(2)

    # ==========================================================
    # RENAME (KEEP YOUR ORIGINAL UI NAMING STYLE)
    # ==========================================================
    rename_map = {
        "symbol_id": "ID",
        "symbol": "Symbol",
        "signal_date": "Date",

        "signal_week_high": "Week High",
        "signal_week_low": "Week Low",
        "signal_week_close": "Week Close",

        "rsi_3": "RSI 3",
        "rsi_9": "RSI 9",
        "ema_rsi_9_3": "EMA RSI",
        "wma_rsi_9_21": "WMA RSI",

        "rsi_9_prev": "PREV RSI 9",
        "wma_prev": "PREV WMA"
    }

    df.rename(columns=rename_map, inplace=True)

    # ==========================================================
    # COLUMN ORDER (STRICT + CLEAN)
    # ==========================================================
    preferred_order = [
        "ID",
        "Symbol",
        "Date",

        "Week High",
        "Week Low",
        "Week Close",

        "RSI 3",
        "RSI 9",
        "EMA RSI",
        "WMA RSI",

        "PREV RSI 9",
        "PREV WMA"
    ]

    cols = [c for c in preferred_order if c in df.columns]

    return df[cols].reset_index(drop=True)