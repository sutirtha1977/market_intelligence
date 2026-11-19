
# database/equity/nse_tables.py

from psycopg2 import sql
from config.logger import log


# =========================================================
# CREATE INDEX CONSTITUENTS TABLE
# =========================================================

def create_index_constituents_table(cur):

    table = "nse_india_index_constituents"

    cur.execute("""
        CREATE TABLE IF NOT EXISTS nse_india_index_constituents (

            index_id INTEGER NOT NULL,
            symbol_id INTEGER NOT NULL,

            weight_pct DOUBLE PRECISION DEFAULT 0,

            PRIMARY KEY (index_id, symbol_id),

            FOREIGN KEY (index_id)
                REFERENCES nse_india_index_symbols(symbol_id)
                ON DELETE CASCADE,

            FOREIGN KEY (symbol_id)
                REFERENCES yahoo_india_equity_symbols(symbol_id)
                ON DELETE CASCADE

        );
    """)

    # -----------------------------------------------------
    # ADD INDEX FOR STOCK-BASED LOOKUPS
    # -----------------------------------------------------

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_nse_constituents_symbol
        ON nse_india_index_constituents(symbol_id);
    """)


# =========================================================
# CREATE INDEX SRT TABLE
# =========================================================

def create_index_srt_table(cur):

    cur.execute("""
        CREATE TABLE IF NOT EXISTS nse_india_index_srt (

            index_id INTEGER NOT NULL,
            timeframe TEXT NOT NULL,
            date DATE NOT NULL,

            srt DOUBLE PRECISION DEFAULT 0,

            PRIMARY KEY (index_id, timeframe, date),

            FOREIGN KEY (index_id)
                REFERENCES nse_india_index_symbols(symbol_id)
                ON DELETE CASCADE

        );
    """)

    # -----------------------------------------------------
    # TIMEFRAME + DATE INDEX
    # -----------------------------------------------------

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_nse_srt_tf_date
        ON nse_india_index_srt(timeframe, date DESC);
    """)


# =========================================================
# CREATE NSE HOLIDAYS TABLE
# =========================================================

def create_nse_holidays_table(cur):

    cur.execute("""
        CREATE TABLE IF NOT EXISTS nse_holidays (

            holiday_date DATE PRIMARY KEY,

            day_name TEXT,

            holiday_name TEXT NOT NULL

        );
    """)


# =========================================================
# CREATE ALL NSE INDEX TABLES
# =========================================================

def create_index_tables(cur):

    try:

        log("========== NSE INDEX TABLE SETUP START ==========")

        # -------------------------------------------------
        # INDEX CONSTITUENTS
        # -------------------------------------------------

        log("📦 Creating nse_india_index_constituents")

        create_index_constituents_table(cur)

        log("✅ Constituents table ready")

        # -------------------------------------------------
        # INDEX SRT
        # -------------------------------------------------

        log("📦 Creating nse_india_index_srt")

        create_index_srt_table(cur)

        log("✅ Index SRT table ready")

        # -------------------------------------------------
        # NSE HOLIDAYS
        # -------------------------------------------------

        log("📦 Creating nse_holidays")

        create_nse_holidays_table(cur)

        log("✅ NSE holidays table ready")

        log("🚀 All NSE index tables created successfully")

    except Exception as e:

        log(f"🔥 ERROR creating NSE index tables: {e}")
        raise
