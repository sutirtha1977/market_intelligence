
# database/equity/scanner.py

from config.logger import log


# =========================================================
# CREATE WEEKLY SCANNER SIGNALS
# =========================================================

def create_weekly_scanner_table(cur):

    cur.execute("""
        CREATE TABLE IF NOT EXISTS scanner_signals_weekly (

            asset_type TEXT NOT NULL,
            scanner_type TEXT NOT NULL,
            symbol_id INTEGER NOT NULL,
            signal_date DATE NOT NULL,

            breakout_high DOUBLE PRECISION,
            breakout_close DOUBLE PRECISION,
            current_close DOUBLE PRECISION,

            rsi_3 DOUBLE PRECISION,
            rsi_9 DOUBLE PRECISION,
            ema_rsi_9_3 DOUBLE PRECISION,
            wma_rsi_9_21 DOUBLE PRECISION,

            is_triggered BOOLEAN NOT NULL DEFAULT FALSE,
            trigger_date DATE,

            PRIMARY KEY (
                asset_type,
                scanner_type,
                symbol_id,
                signal_date
            )

        );
    """)

    # -----------------------------------------------------
    # PENDING SIGNALS
    # -----------------------------------------------------

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_sws_pending
        ON scanner_signals_weekly (
            asset_type,
            scanner_type,
            signal_date DESC
        )
        WHERE is_triggered = FALSE;
    """)


# =========================================================
# CREATE UNIFIED SCANNER SIGNALS
# =========================================================

def create_unified_scanner_table(cur):

    cur.execute("""
        CREATE TABLE IF NOT EXISTS scanner_signals (

            asset_type TEXT NOT NULL,
            scanner_type TEXT NOT NULL,
            scanner_freq TEXT NOT NULL,

            symbol_id INTEGER NOT NULL,
            signal_date DATE NOT NULL,

            breakout_high DOUBLE PRECISION,
            breakout_close DOUBLE PRECISION,
            current_close DOUBLE PRECISION,

            rsi_3 DOUBLE PRECISION,
            rsi_9 DOUBLE PRECISION,
            ema_rsi_9_3 DOUBLE PRECISION,
            wma_rsi_9_21 DOUBLE PRECISION,

            PRIMARY KEY (
                asset_type,
                scanner_type,
                scanner_freq,
                symbol_id,
                signal_date
            )

        );
    """)

    # -----------------------------------------------------
    # SCANNER QUERY INDEX
    # -----------------------------------------------------

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_ss_scan
        ON scanner_signals (
            asset_type,
            scanner_type,
            scanner_freq,
            signal_date DESC
        );
    """)

    # -----------------------------------------------------
    # SYMBOL HISTORY INDEX
    # -----------------------------------------------------

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_ss_symbol
        ON scanner_signals (
            symbol_id,
            signal_date DESC
        );
    """)


# =========================================================
# CREATE ALL SCANNER TABLES
# =========================================================

def create_scanner_tables(cur):

    try:

        log("========== SCANNER TABLE SETUP START ==========")

        # -------------------------------------------------
        # WEEKLY SCANNER
        # -------------------------------------------------

        log("📦 Creating scanner_signals_weekly")

        create_weekly_scanner_table(cur)

        log("✅ Weekly scanner table ready")

        # -------------------------------------------------
        # UNIFIED SCANNER
        # -------------------------------------------------

        log("📦 Creating scanner_signals")

        create_unified_scanner_table(cur)

        log("✅ Unified scanner table ready")

        log("🚀 All scanner tables created successfully")

    except Exception as e:

        log(f"🔥 ERROR creating scanner tables: {e}")
        raise
