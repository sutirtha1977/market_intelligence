
import pandas as pd

from psycopg2 import sql
from psycopg2.extras import execute_values

from config.logger import log
from database.connection import get_db_connection_cm
from config.db_config import SYMBOL_MAPPING
from config.paths import SYMBOLS_MASTER

from database.equity.price import PRICE_TABLES
from database.equity.indicators import INDICATOR_TABLES


# =========================================================
# DEPENDENCY TABLE MAPPINGS
# =========================================================

PRICE_TABLE_MAPPING = {
    symbol_table: f"{prefix}_price"
    for prefix, symbol_table in PRICE_TABLES
}

INDICATOR_TABLE_MAPPING = {
    symbol_table: f"{prefix}_indicators"
    for prefix, symbol_table in INDICATOR_TABLES
}


# =========================================================
# PREPARE SYMBOL RECORDS
# =========================================================

def prepare_symbol_records(
    table_name: str,
    df: pd.DataFrame,
    columns: list[str],
):
    """
    Validate and prepare symbol records before database changes.
    """

    # Work on a copy; do not modify the original DataFrame.
    data = df.copy()

    # Normalize Excel column names.
    data.columns = [
        str(col).lower().strip()
        for col in data.columns
    ]

    if data.columns.duplicated().any():
        raise ValueError(
            f"Duplicate Excel column names found for {table_name}"
        )

    # Normalize configured columns.
    configured_columns = [
        col.lower().strip()
        for col in columns
    ]

    available_cols = [
        col for col in configured_columns
        if col in data.columns
    ]

    if not available_cols:
        raise ValueError(
            f"No matching columns found for {table_name}"
        )

    # Determine unique conflict key.
    if "symbol" in available_cols and "exchange" in available_cols:

        conflict_cols = ["symbol", "exchange"]

    elif "symbol" in available_cols:

        conflict_cols = ["symbol"]

    else:

        raise ValueError(
            f"Symbol conflict key missing for {table_name}"
        )

    # Select required columns.
    data = data[available_cols].copy()

    # Remove rows with missing conflict keys.
    if data[conflict_cols].isna().any().any():
        raise ValueError(
            f"Missing symbol conflict key values in {table_name}"
        )

    # Remove whitespace-only symbol and exchange values.
    for col in conflict_cols:
        data[col] = data[col].astype("string").str.strip()

        if data[col].isna().any() or data[col].eq("").any():
            raise ValueError(
                f"Empty {col} values found in {table_name}"
            )

    # Keep the last record for duplicate conflict keys.
    data.drop_duplicates(
        subset=conflict_cols,
        keep="last",
        inplace=True
    )

    if data.empty:
        raise ValueError(
            f"No valid symbol records found for {table_name}"
        )

    # Convert pandas missing values to Python None (SQL NULL).
    data = data.astype(object).where(pd.notna(data), None)

    records = list(
        data.itertuples(index=False, name=None)
    )

    return available_cols, conflict_cols, records


# =========================================================
# TRUNCATE RELATED PRICE AND INDICATOR TABLES
# =========================================================

def truncate_symbol_dependencies(
    conn,
    symbol_table: str,
) -> None:

    price_table = PRICE_TABLE_MAPPING.get(symbol_table)
    indicator_table = INDICATOR_TABLE_MAPPING.get(symbol_table)

    if not price_table or not indicator_table:
        raise ValueError(
            f"Price or indicator table mapping missing "
            f"for symbol table: {symbol_table}"
        )

    try:

        table_ids = sql.SQL(", ").join([
            sql.Identifier(price_table),
            sql.Identifier(indicator_table),
        ])

        with conn.cursor() as cur:

            # Truncate both dependent tables together.
            cur.execute(
                sql.SQL("TRUNCATE TABLE {}").format(table_ids)
            )

        log(
            f"🗑️ Truncated dependent tables | "
            f"Price: {price_table} | "
            f"Indicators: {indicator_table}"
        )

    except Exception as e:

        log(
            f"❌ Failed truncating dependent tables "
            f"for {symbol_table}: {e}"
        )

        raise


# =========================================================
# UPSERT INDIVIDUAL SYMBOL TABLE
# =========================================================

def refresh_one_symbol_table(
    table_name: str,
    df: pd.DataFrame,
    columns: list[str],
    conn,
) -> int:

    try:

        log(f"========== REFRESHING {table_name} ==========")

        # -------------------------------------------------
        # PREPARE AND VALIDATE RECORDS
        # -------------------------------------------------

        available_cols, conflict_cols, records = (
            prepare_symbol_records(
                table_name=table_name,
                df=df,
                columns=columns,
            )
        )

        log(
            f"Prepared {len(records)} unique symbol records "
            f"for {table_name}"
        )

        # -------------------------------------------------
        # TRUNCATE PRICE AND INDICATOR TABLES
        # -------------------------------------------------

        truncate_symbol_dependencies(
            conn=conn,
            symbol_table=table_name,
        )

        # -------------------------------------------------
        # BUILD SAFE UPSERT QUERY
        # -------------------------------------------------

        table_id = sql.Identifier(table_name)

        column_ids = sql.SQL(", ").join(
            sql.Identifier(col)
            for col in available_cols
        )

        conflict_ids = sql.SQL(", ").join(
            sql.Identifier(col)
            for col in conflict_cols
        )

        update_cols = [
            col for col in available_cols
            if col not in conflict_cols
        ]

        if update_cols:

            set_clause = sql.SQL(", ").join(
                sql.SQL("{} = EXCLUDED.{}").format(
                    sql.Identifier(col),
                    sql.Identifier(col),
                )
                for col in update_cols
            )

            conflict_action = sql.SQL(
                "DO UPDATE SET {}"
            ).format(set_clause)

        else:

            conflict_action = sql.SQL("DO NOTHING")

        insert_query = sql.SQL("""
            INSERT INTO {} ({})
            VALUES %s
            ON CONFLICT ({})
            {}
        """).format(
            table_id,
            column_ids,
            conflict_ids,
            conflict_action,
        )

        # -------------------------------------------------
        # BULK UPSERT
        # -------------------------------------------------

        with conn.cursor() as cur:

            execute_values(
                cur,
                insert_query.as_string(conn),
                records,
                page_size=1000,
            )

        log(
            f"✅ {table_name}: "
            f"{len(records)} symbols refreshed successfully"
        )

        log(
            f"========== {table_name} REFRESH COMPLETE =========="
        )

        return len(records)

    except Exception as e:

        log(
            f"❌ Error refreshing symbol table "
            f"{table_name}: {e}"
        )

        raise


# =========================================================
# REFRESH ALL SYMBOL TABLES
# =========================================================

def refresh_symbols() -> None:

    try:

        log("========== SYMBOL REFRESH START ==========")

        log(
            f"Excel source: {SYMBOLS_MASTER}"
        )

        total_records = 0
        successful_tables = 0
        skipped_tables = 0

        # -------------------------------------------------
        # LOAD EXCEL WORKBOOK ONCE
        # -------------------------------------------------

        with pd.ExcelFile(SYMBOLS_MASTER) as xls:

            available_sheets = set(xls.sheet_names)

            log(
                f"Excel workbook loaded | "
                f"Worksheets: {len(available_sheets)}"
            )

            # -------------------------------------------------
            # DATABASE TRANSACTION
            # -------------------------------------------------

            with get_db_connection_cm() as conn:

                for sheet_name, table_name, columns in SYMBOL_MAPPING:

                    try:

                        # -------------------------------------
                        # CHECK WORKSHEET
                        # -------------------------------------

                        if sheet_name not in available_sheets:

                            log(
                                f"⚠️ Skipped {table_name}: "
                                f"Worksheet '{sheet_name}' not found"
                            )

                            skipped_tables += 1
                            continue

                        # -------------------------------------
                        # READ WORKSHEET
                        # -------------------------------------

                        df = xls.parse(
                            sheet_name=sheet_name
                        )

                        if df.empty:

                            log(
                                f"⚠️ Skipped {table_name}: "
                                "Worksheet is empty. "
                                "Existing data retained."
                            )

                            skipped_tables += 1
                            continue

                        # -------------------------------------
                        # REFRESH SYMBOL TABLE
                        # -------------------------------------

                        inserted_records = refresh_one_symbol_table(
                            table_name=table_name,
                            df=df,
                            columns=columns,
                            conn=conn,
                        )

                        total_records += inserted_records
                        successful_tables += 1

                    except Exception as e:

                        log(
                            f"❌ Symbol refresh failed for "
                            f"{table_name}: {e}"
                        )

                        raise

        # -------------------------------------------------
        # SUCCESS LOGGING
        # -------------------------------------------------

        log(
            f"✅ SYMBOL REFRESH COMPLETED | "
            f"Tables refreshed: {successful_tables} | "
            f"Tables skipped: {skipped_tables} | "
            f"Symbols processed: {total_records}"
        )

        log("========== SYMBOL REFRESH END ==========")

    except Exception as e:

        log(
            f"❌ Full symbol refresh failed: {e}"
        )

        raise


# --------------------------------------------------------------------------
