# database/equity/nse_tables.py

from config.logger import log

def create_index_tables(cur):

    try:
        log("🚀 Creating index tables...")

        # ==========================================================
        # INDEX CONSTITUENTS (RELATIONSHIP TABLE)
        # ==========================================================
        cur.execute("""
        CREATE TABLE IF NOT EXISTS nse_india_index_constituents (
            index_id INTEGER,
            symbol_id INTEGER,
            weight_pct REAL,
            PRIMARY KEY(index_id, symbol_id),

            FOREIGN KEY(index_id)
                REFERENCES nse_india_index_symbols(symbol_id),

            FOREIGN KEY(symbol_id)
                REFERENCES yahoo_india_equity_symbols(symbol_id)
        );
        """)

        # ==========================================================
        # INDEX SRT (TIME SERIES + FK ON INDEX)
        # ==========================================================
        cur.execute("""
        CREATE TABLE IF NOT EXISTS nse_india_index_srt (
            index_id INTEGER,
            timeframe TEXT,
            date DATE,
            srt REAL,
            PRIMARY KEY(index_id, timeframe, date),

            FOREIGN KEY(index_id)
                REFERENCES nse_india_index_symbols(symbol_id)
        );
        """)

        # ==========================================================
        # INDEX PERFORMANCE INDEX
        # ==========================================================
        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_nse_srt_tf_date 
        ON nse_india_index_srt(timeframe, date DESC);
        """)

        # ==========================================================
        # HOLIDAYS TABLE (NO FK NEEDED)
        # ==========================================================
        cur.execute("""
        CREATE TABLE IF NOT EXISTS holidays_nse (
            holiday_date DATE PRIMARY KEY,
            day_name TEXT,
            holiday_name TEXT
        );
        """)

        log("✅ Index tables created successfully")

    except Exception as e:
        log(f"❌ ERROR creating index tables: {e}")
        raise