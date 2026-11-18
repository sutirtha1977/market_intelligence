# database/equity/smc.py

from config.logger import log

def create_smc_tables(cur):

    try:

        cur.execute("""
        CREATE TABLE IF NOT EXISTS yahoo_india_equity_smc_swings (
            symbol_id INTEGER,
            timeframe TEXT,
            date DATE,
            swing_type SMALLINT,
            price REAL,
            is_internal BOOLEAN DEFAULT FALSE,
            PRIMARY KEY(symbol_id, timeframe, date, is_internal)
        );
        """)

        log("📦 Created smc_swings")

        cur.execute("""
        CREATE TABLE IF NOT EXISTS yahoo_india_equity_smc_structure (
            symbol_id INTEGER,
            timeframe TEXT,
            date DATE,
            structure_type SMALLINT,
            direction SMALLINT,
            is_internal BOOLEAN DEFAULT FALSE,
            break_price REAL,
            reference_price REAL,
            PRIMARY KEY(symbol_id, timeframe, date, structure_type, is_internal)
        );
        """)

        log("📦 Created smc_structure")

        cur.execute("""
        CREATE TABLE IF NOT EXISTS yahoo_india_equity_smc_order_blocks (
            symbol_id INTEGER,
            timeframe TEXT,
            created_date DATE,
            ob_type SMALLINT,
            top REAL,
            bottom REAL,
            mitigated BOOLEAN DEFAULT FALSE,
            mitigated_date DATE,
            strength REAL,
            PRIMARY KEY(symbol_id, timeframe, created_date, ob_type)
        );
        """)

        log("📦 Created smc_order_blocks")

        cur.execute("""
        CREATE TABLE IF NOT EXISTS yahoo_india_equity_smc_fvg (
            symbol_id INTEGER,
            timeframe TEXT,
            start_date DATE,
            end_date DATE,
            gap_top REAL,
            gap_bottom REAL,
            fvg_type SMALLINT,
            filled BOOLEAN DEFAULT FALSE,
            filled_date DATE,
            PRIMARY KEY(symbol_id, timeframe, start_date, end_date)
        );
        """)

        log("📦 Created smc_fvg")

        cur.execute("""
        CREATE TABLE IF NOT EXISTS yahoo_india_equity_smc_equal_levels (
            symbol_id INTEGER,
            timeframe TEXT,
            date DATE,
            level REAL,
            level_type SMALLINT,
            tolerance REAL,
            PRIMARY KEY(symbol_id, timeframe, date, level_type)
        );
        """)

        log("📦 Created smc_equal_levels")

        cur.execute("""
        CREATE TABLE IF NOT EXISTS yahoo_india_equity_smc_snapshot (
            symbol_id INTEGER,
            timeframe TEXT,
            date DATE,
            trend SMALLINT,
            last_bos_date DATE,
            last_choch_date DATE,
            active_bullish_ob BOOLEAN,
            active_bearish_ob BOOLEAN,
            active_bullish_fvg BOOLEAN,
            active_bearish_fvg BOOLEAN,
            PRIMARY KEY(symbol_id, timeframe, date)
        );
        """)

        log("📦 Created smc_snapshot")

        log("✅ SMC tables created successfully")

    except Exception as e:
        log(f"🔥 ERROR in create_smc_tables: {e}")
        raise