# database/create_equity_database.py

from config.logger import log
from database.connection import get_db_connection, close_db_connection

from database.equity.drop_tables import drop_all_tables
from database.equity.currency import create_currency_master
from database.equity.symbols import create_symbol_tables
from database.equity.price import create_price_tables
from database.equity.indicators import create_indicator_tables
from database.equity.nse_tables import create_index_tables
from database.equity.scanner import create_scanner_tables
from database.equity.smc import create_smc_tables
from database.equity.vix import create_vix_table
from database.equity.vcp_tables import create_vcp_tables
# from database.equity.post_setup import run_post_setup

def create_equity_database(drop_existing=False):
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        log("========== DATABASE SETUP START ==========")

        if drop_existing:
            drop_all_tables(cur, conn)

        create_currency_master(cur)
        create_symbol_tables(cur)
        create_price_tables(cur)
        create_indicator_tables(cur)
        create_index_tables(cur)
        create_vix_table(cur)
        create_scanner_tables(cur)
        create_smc_tables(cur)
        create_vcp_tables(cur)

        conn.commit()

        # 🔥 CRITICAL POST OPTIMIZATION
        # run_post_setup(cur)

        log("========== DATABASE SETUP COMPLETE ==========")

    except Exception as e:
        conn.rollback()
        log(f"ERROR: {e}")
        raise

    finally:
        close_db_connection(conn)