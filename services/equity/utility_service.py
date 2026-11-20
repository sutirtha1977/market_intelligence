import pandas as pd

from psycopg2 import sql
from psycopg2.extras import execute_values

from database.connection import get_db_connection_cm
from config.db_config import ASSET_TABLE_CONFIG
from config.paths import NSE_HOLIDAYS
from config.logger import log

# --------------------------------------------------------------------------
# def get_latest_symbol_dates(asset_type: str, table_type: str = "price") -> pd.DataFrame:
#     try:
#         tables = ASSET_TABLE_CONFIG[asset_type]
#         symbol_table = tables["symbol"]
#         price_table = tables["price"]
#         indicator_table = tables["indicator"]

#         table_name = price_table if table_type == "price" else indicator_table
#         log(f"DEBUG: Fetching latest dates | symbol_table={symbol_table} | data_table={table_name}")
#         engine = get_engine()  # SQLAlchemy engine for read queries
#         df = pd.read_sql(f"""
#             SELECT 
#                 s.symbol,
#                 MAX(CASE WHEN p.timeframe = '1d'  THEN p.date END) AS latest_1d,
#                 MAX(CASE WHEN p.timeframe = '1wk' THEN p.date END) AS latest_1wk,
#                 MAX(CASE WHEN p.timeframe = '1mo' THEN p.date END) AS latest_1mo
#             FROM {table_name} p
#             JOIN {symbol_table} s ON s.symbol_id = p.symbol_id
#             GROUP BY s.symbol
#             ORDER BY s.symbol
#         """, engine)
#         log(f"DEBUG: Rows fetched from {table_name}: {len(df)}")
#         for col in ["latest_1d", "latest_1wk", "latest_1mo"]:
#             df[col] = df[col].apply(lambda x: x.strftime("%Y-%m-%d") if pd.notnull(x) else "-")
#         df["symbol"] = df["symbol"].str.replace(".NS", "", regex=False)
#         df.rename(columns={
#             "symbol": "Symbol",
#             "latest_1d": "Daily",
#             "latest_1wk": "Weekly",
#             "latest_1mo": "Monthly",
#         }, inplace=True)
#         return df[["Symbol", "Daily", "Weekly", "Monthly"]]
#     except Exception as e:
#         log(f"❌ Failed to fetch latest symbol dates for {asset_type}: {e}")
#         return pd.DataFrame()
# --------------------------------------------------------------------------
# =========================================================
# UPSERT NSE HOLIDAYS
# =========================================================

def upsert_nse_holidays() -> None:
    try:
        log("========== NSE HOLIDAYS REFRESH START ==========")
        # -------------------------------------------------
        # GET TABLE CONFIGURATION
        # -------------------------------------------------
        holidays_table = ASSET_TABLE_CONFIG["reference"]["nse_holidays"]
        table_id = sql.Identifier(holidays_table)
        # -------------------------------------------------
        # READ CSV
        # -------------------------------------------------
        df = pd.read_csv(NSE_HOLIDAYS)
        if df.empty:
            log(
                "⚠️ NSE holidays CSV is empty. "
                "Existing database data retained."
            )
            return
        # -------------------------------------------------
        # VALIDATE CSV COLUMNS
        # -------------------------------------------------
        required_columns = ["Date", "Day", "Holiday"]
        missing_columns = [
            col for col in required_columns
            if col not in df.columns
        ]
        if missing_columns:
            raise ValueError(
                f"Missing columns in NSE holidays CSV: {missing_columns}"
            )
        # -------------------------------------------------
        # VALIDATE AND CONVERT DATES
        # -------------------------------------------------
        df["holiday_date"] = pd.to_datetime(
            df["Date"],
            format="%d/%m/%y",
            errors="coerce"
        )
        if df["holiday_date"].isnull().any():
            invalid_count = int(df["holiday_date"].isnull().sum())
            raise ValueError(
                f"Found {invalid_count} invalid holiday dates in CSV"
            )
        df["holiday_date"] = df["holiday_date"].dt.date
        # -------------------------------------------------
        # CLEAN DATA
        # -------------------------------------------------
        df["Day"] = df["Day"].astype("string").str.strip()
        df["Holiday"] = df["Holiday"].astype("string").str.strip()
        # Holiday name is NOT NULL in PostgreSQL.
        if df["Holiday"].isna().any() or df["Holiday"].eq("").any():
            raise ValueError("Holiday name cannot be empty")

        # Convert empty optional day names to NULL.
        df["Day"] = df["Day"].replace("", pd.NA)

        # Remove duplicate dates, keeping the last CSV entry.
        df.drop_duplicates(
            subset=["holiday_date"],
            keep="last",
            inplace=True
        )
        # -------------------------------------------------
        # PREPARE BULK INSERT RECORDS
        # -------------------------------------------------
        records = [
            (
                row.holiday_date,
                None if pd.isna(row.Day) else str(row.Day),
                str(row.Holiday)
            )
            for row in df[
                ["holiday_date", "Day", "Holiday"]
            ].itertuples(index=False)
        ]

        if not records:
            log(
                "⚠️ No valid NSE holiday records found. "
                "Existing database data retained."
            )
            return

        # -------------------------------------------------
        # PREPARE INSERT QUERY
        # -------------------------------------------------
        insert_query = sql.SQL("""
            INSERT INTO {} (
                holiday_date,
                day_name,
                holiday_name
            )
            VALUES %s
            ON CONFLICT (holiday_date)
            DO UPDATE SET
                day_name = EXCLUDED.day_name,
                holiday_name = EXCLUDED.holiday_name;
        """).format(table_id)

        # -------------------------------------------------
        # TRUNCATE AND BULK INSERT
        # -------------------------------------------------
        with get_db_connection_cm() as conn:
            with conn.cursor() as cur:
                # Step 1: Clear existing records.
                cur.execute(
                    sql.SQL("TRUNCATE TABLE {}").format(table_id)
                )
                log(
                    f"🗑️ Existing records truncated: {holidays_table}"
                )
                # Step 2: Insert fresh records.
                execute_values(
                    cur,
                    insert_query.as_string(conn),
                    records,
                    page_size=500
                )
        # -------------------------------------------------
        # SUCCESS LOGGING
        # -------------------------------------------------
        log(
            f"✅ NSE holidays refresh completed | "
            f"Records inserted: {len(records)}"
        )
        log("========== NSE HOLIDAYS REFRESH COMPLETE ==========")

    except Exception as e:
        log(f"❌ Failed to refresh NSE holidays: {e}")
        raise

# --------------------------------------------------------------------------