import pandas as pd
import traceback

from config.logger import log
from database.connection import get_db_connection_cm
from config.db_config import SYMBOL_MAPPING
from config.paths import SYMBOLS_MASTER  # Path to symbols_master.xlsx

# --------------------------------------------------------------------------
def refresh_one_symbol_table(
    table_name: str,
    df: pd.DataFrame,
    columns: list[str],
    conn,
) -> None:
    try:
        log(f"Refreshing {table_name} with columns: {columns}")
        df.columns = [c.lower().strip() for c in df.columns]
        available_cols = [c for c in columns if c in df.columns]
        if not available_cols:
            log(f"No matching columns found for {table_name}")
            return
        df = df[available_cols].drop_duplicates()
        records = [tuple(r) for r in df.to_numpy()]
        if not records:
            log(f"No records found for {table_name}")
            return
        col_names = ", ".join(available_cols)
        placeholders = ", ".join(["%s"] * len(available_cols))
        if "symbol" in available_cols and "exchange" in available_cols:
            conflict_cols = ["symbol", "exchange"]
        elif "symbol" in available_cols:
            conflict_cols = ["symbol"]
        else:
            conflict_cols = [available_cols[0]]
        conflict_cols_str = ", ".join(conflict_cols)
        set_clause = ", ".join([f"{c} = EXCLUDED.{c}" for c in available_cols if c not in conflict_cols])
        with conn.cursor() as cur:
            cur.executemany(
                f"""
                INSERT INTO {table_name} ({col_names})
                VALUES ({placeholders})
                ON CONFLICT ({conflict_cols_str}) DO UPDATE
                SET {set_clause}
                """,
                records,
            )
        log(f"✅ {table_name}: {len(records)} symbols refreshed")
    except Exception as e:
        log(f"❌ Error refreshing {table_name}: {e}")
        traceback.print_exc()
        raise
# --------------------------------------------------------------------------
def refresh_symbols() -> None:
    log(f"Starting full symbol refresh from Excel: {SYMBOLS_MASTER}")
    try:
        with get_db_connection_cm() as conn: 
            xls = pd.ExcelFile(SYMBOLS_MASTER)
            log(f"Excel file loaded with sheets: {xls.sheet_names}")
            for sheet_name, table_name, columns in SYMBOL_MAPPING:
                try:
                    if sheet_name not in xls.sheet_names:
                        log(f"Skipped {table_name}: worksheet '{sheet_name}' not found in Excel")
                        continue
                    df = pd.read_excel(SYMBOLS_MASTER, sheet_name=sheet_name)
                    refresh_one_symbol_table(table_name, df, columns, conn)
                except Exception as e:
                    log(f"Skipped {table_name} due to error: {e}")
                    traceback.print_exc()
        log("✅ Symbol refresh completed")
    except Exception as e:
        log(f"❌ Full symbol refresh failed: {e}")
        traceback.print_exc()
# --------------------------------------------------------------------------