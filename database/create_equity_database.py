
# database/create_equity_database.py

from config.logger import log

from database.connection import (
    get_db_connection,
    close_db_connection,
)

from database.equity.drop_tables import drop_all_tables
from database.equity.currency import create_currency_master
from database.equity.symbols import create_symbol_tables
from database.equity.price import create_price_tables
from database.equity.indicators import create_indicator_tables
from database.equity.nse_tables import create_index_tables
# from database.equity.scanner import create_scanner_tables
from database.equity.vix import create_vix_table

# Enable these imports when their setup functions are ready.
# from database.equity.smc import create_smc_tables
# from database.equity.vcp_tables import create_vcp_tables
# from database.equity.post_setup import run_post_setup


def create_equity_database(drop_existing=False):

    conn = None
    cur = None

    try:
        log("========== DATABASE SETUP START ==========")

        # -------------------------------------------------
        # DATABASE CONNECTION
        # -------------------------------------------------

        conn = get_db_connection()
        cur = conn.cursor()

        # -------------------------------------------------
        # DROP EXISTING TABLES
        # -------------------------------------------------

        if drop_existing:
            log("⚠️ Dropping existing equity database tables...")
            drop_all_tables(cur, conn)

        # -------------------------------------------------
        # MASTER TABLES
        # -------------------------------------------------

        log("========== CREATING MASTER TABLES ==========")

        create_currency_master(cur)

        # -------------------------------------------------
        # SYMBOL TABLES
        # -------------------------------------------------

        log("========== CREATING SYMBOL TABLES ==========")

        create_symbol_tables(cur)

        # -------------------------------------------------
        # PRICE TABLES
        # -------------------------------------------------

        log("========== CREATING PRICE TABLES ==========")

        create_price_tables(cur)

        # -------------------------------------------------
        # INDICATOR TABLES
        # -------------------------------------------------

        log("========== CREATING INDICATOR TABLES ==========")

        create_indicator_tables(cur)

        # -------------------------------------------------
        # MARKET / INDEX TABLES
        # -------------------------------------------------

        log("========== CREATING INDEX TABLES ==========")

        create_index_tables(cur)

        # -------------------------------------------------
        # VIX TABLES
        # -------------------------------------------------

        log("========== CREATING VIX TABLES ==========")

        create_vix_table(cur)

        # -------------------------------------------------
        # SCANNER TABLES
        # -------------------------------------------------

        # log("========== CREATING SCANNER TABLES ==========")

        # create_scanner_tables(cur)

        # -------------------------------------------------
        # OPTIONAL TABLES
        # -------------------------------------------------

        # create_smc_tables(cur)
        # create_vcp_tables(cur)

        # -------------------------------------------------
        # POST DATABASE SETUP
        # -------------------------------------------------

        # run_post_setup(cur)

        # -------------------------------------------------
        # COMMIT TRANSACTION
        # -------------------------------------------------

        conn.commit()

        log("✅ DATABASE TRANSACTION COMMITTED")
        log("========== DATABASE SETUP COMPLETE ==========")

    except Exception as e:

        if conn is not None:
            try:
                conn.rollback()
                log("⚠️ Database transaction rolled back")
            except Exception as rollback_error:
                log(f"❌ Database rollback failed: {rollback_error}")

        log(f"🔥 ERROR creating equity database: {e}")

        raise

    finally:

        # -------------------------------------------------
        # CLOSE CURSOR
        # -------------------------------------------------

        if cur is not None:
            try:
                cur.close()
            except Exception as e:
                log(f"⚠️ Error closing database cursor: {e}")

        # -------------------------------------------------
        # RELEASE DATABASE CONNECTION
        # -------------------------------------------------

        if conn is not None:
            try:
                close_db_connection(conn)
            except Exception as e:
                log(f"❌ Error releasing database connection: {e}")
