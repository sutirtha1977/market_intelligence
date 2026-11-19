
# database/equity/drop_tables.py

from psycopg2 import sql
from config.logger import log


# =========================================================
# TABLES TO DROP
# Child tables are listed before parent tables.
# =========================================================

TABLES_TO_DROP = [

    # -----------------------------------------------------
    # CURRENCY
    # -----------------------------------------------------

    "currency_master",

    # -----------------------------------------------------
    # NSE TABLES
    # -----------------------------------------------------

    "nse_india_index_constituents",
    "nse_india_index_srt",
    "nse_holidays",

    # -----------------------------------------------------
    # SCANNER TABLES
    # -----------------------------------------------------

    "scanner_signals_weekly",
    "scanner_signals",

    # -----------------------------------------------------
    # VIX
    # -----------------------------------------------------

    "nse_vix_features",

    # -----------------------------------------------------
    # PRICE TABLES
    # -----------------------------------------------------

    "yahoo_india_equity_price",
    "yahoo_india_index_price",
    "nse_india_index_price",
    "yahoo_usa_equity_price",
    "yahoo_global_index_price",
    "yahoo_commodity_price",
    "yahoo_crypto_price",
    "yahoo_forex_price",

    # -----------------------------------------------------
    # INDICATOR TABLES
    # -----------------------------------------------------

    "yahoo_india_equity_indicators",
    "yahoo_india_index_indicators",
    "nse_india_index_indicators",
    "yahoo_usa_equity_indicators",
    "yahoo_global_index_indicators",
    "yahoo_commodity_indicators",
    "yahoo_crypto_indicators",
    "yahoo_forex_indicators",

    # -----------------------------------------------------
    # SMC TABLES
    # -----------------------------------------------------

    "yahoo_india_equity_smc_structure",
    "yahoo_india_equity_smc_swings",
    "yahoo_india_equity_smc_order_blocks",
    "yahoo_india_equity_smc_fvg",
    "yahoo_india_equity_smc_equal_levels",
    "yahoo_india_equity_smc_snapshot",

    # -----------------------------------------------------
    # SYMBOL TABLES (PARENT TABLES)
    # -----------------------------------------------------

    "yahoo_india_equity_symbols",
    "yahoo_india_index_symbols",
    "nse_india_index_symbols",
    "yahoo_usa_equity_symbols",
    "yahoo_global_index_symbols",
    "yahoo_commodity_symbols",
    "yahoo_crypto_symbols",
    "yahoo_forex_symbols",
]


# =========================================================
# DROP ALL TABLES
# =========================================================

def drop_all_tables(cur, conn):

    try:

        log("========== DATABASE DROP START ==========")

        total = len(TABLES_TO_DROP)

        for index, table in enumerate(TABLES_TO_DROP, start=1):

            log(f"🗑️ Dropping table ({index}/{total}): {table}")

            cur.execute(
                sql.SQL("DROP TABLE IF EXISTS {} CASCADE").format(
                    sql.Identifier(table)
                )
            )

            log(f"✅ Dropped: {table}")

        log(
            f"🚀 DATABASE DROP COMPLETED | "
            f"Tables processed: {total}"
        )

        # Transaction is managed by create_equity_database().
        # Do not commit here.

    except Exception as e:

        log(f"🔥 ERROR dropping database tables: {e}")
        raise
