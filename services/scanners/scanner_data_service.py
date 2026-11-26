# services/scanners/scanner_data_service.py

import pandas as pd
from database.connection import get_engine
from config.db_config import ASSET_TABLE_CONFIG


# =========================================================
# FETCH SCANNER DATA
# =========================================================
def fetch_scanner_data(
    asset_type: str,
    scanner_type: str,
    scanner_table_map: str
) -> pd.DataFrame:

    # -----------------------------------------------------
    # ENGINE
    # -----------------------------------------------------
    engine = get_engine()

    # -----------------------------------------------------
    # SCANNER TABLE (from config)
    # -----------------------------------------------------
    scanner_table = ASSET_TABLE_CONFIG["scanner"].get(scanner_table_map)

    if not scanner_table:
        raise ValueError(f"Invalid scanner_table_map: {scanner_table_map}")

    # -----------------------------------------------------
    # ASSET TABLES
    # -----------------------------------------------------
    tables = ASSET_TABLE_CONFIG.get(asset_type)

    if not tables:
        raise ValueError(f"Invalid asset_type: {asset_type}")

    symbol_table = tables["symbol"]

    # -----------------------------------------------------
    # SQL
    # -----------------------------------------------------
    sql = f"""
    SELECT
        s.*,
        sym.symbol,
        sym.name
    FROM {scanner_table} s
    JOIN {symbol_table} sym
        ON sym.symbol_id = s.symbol_id
    WHERE s.asset_type = %s
      AND s.scanner_type = %s
    ORDER BY s.signal_date DESC;
    """

    # -----------------------------------------------------
    # EXECUTE
    # -----------------------------------------------------
    return pd.read_sql(
        sql,
        engine,
        params=(
            asset_type,
            scanner_type
        )
    )