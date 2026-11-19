import pandas as pd
from database.connection import get_db_connection_cm, get_engine
from config.db_config import ASSET_TABLE_CONFIG
from config.paths import NSE_HOLIDAYS
from config.logger import log

# --------------------------------------------------------------------------
def get_latest_symbol_dates(asset_type: str, table_type: str = "price") -> pd.DataFrame:
    try:
        tables = ASSET_TABLE_CONFIG[asset_type]
        symbol_table = tables["symbol"]
        price_table = tables["price"]
        indicator_table = tables["indicator"]

        table_name = price_table if table_type == "price" else indicator_table
        log(f"DEBUG: Fetching latest dates | symbol_table={symbol_table} | data_table={table_name}")
        engine = get_engine()  # SQLAlchemy engine for read queries
        df = pd.read_sql(f"""
            SELECT 
                s.symbol,
                MAX(CASE WHEN p.timeframe = '1d'  THEN p.date END) AS latest_1d,
                MAX(CASE WHEN p.timeframe = '1wk' THEN p.date END) AS latest_1wk,
                MAX(CASE WHEN p.timeframe = '1mo' THEN p.date END) AS latest_1mo
            FROM {table_name} p
            JOIN {symbol_table} s ON s.symbol_id = p.symbol_id
            GROUP BY s.symbol
            ORDER BY s.symbol
        """, engine)
        log(f"DEBUG: Rows fetched from {table_name}: {len(df)}")
        for col in ["latest_1d", "latest_1wk", "latest_1mo"]:
            df[col] = df[col].apply(lambda x: x.strftime("%Y-%m-%d") if pd.notnull(x) else "-")
        df["symbol"] = df["symbol"].str.replace(".NS", "", regex=False)
        df.rename(columns={
            "symbol": "Symbol",
            "latest_1d": "Daily",
            "latest_1wk": "Weekly",
            "latest_1mo": "Monthly",
        }, inplace=True)
        return df[["Symbol", "Daily", "Weekly", "Monthly"]]
    except Exception as e:
        log(f"❌ Failed to fetch latest symbol dates for {asset_type}: {e}")
        return pd.DataFrame()
# --------------------------------------------------------------------------
def upsert_nse_holidays() -> None:
    try:
        holidays_table = ASSET_TABLE_CONFIG["reference"]["holidays_nse"]
        df = pd.read_csv(NSE_HOLIDAYS)
        if df.empty:
            log("⚠ NSE holidays CSV is empty")
            return
        df["holiday_date"] = pd.to_datetime(df["Date"], format="%d/%m/%y", errors="coerce")
        if df["holiday_date"].isnull().any():
            raise ValueError("Invalid holiday dates in CSV")
        with get_db_connection_cm() as conn:
            with conn.cursor() as cur:
                for _, row in df.iterrows():
                    cur.execute(f"""
                        INSERT INTO {holidays_table} (holiday_date, day_name, holiday_name)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (holiday_date)
                        DO UPDATE SET
                            day_name = EXCLUDED.day_name,
                            holiday_name = EXCLUDED.holiday_name
                    """, (row["holiday_date"], row["Day"], row["Holiday"]))
        log(f"✅ NSE holidays loaded ({len(df)} rows)")
    except Exception as e:
        log(f"❌ Failed to load NSE holidays: {e}")
        raise
# --------------------------------------------------------------------------