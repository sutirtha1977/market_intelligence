# database/equity/scanner.py

from config.logger import log

def create_scanner_tables(cur):

    try:

        # =====================================================
        # WEEKLY SCANNER SIGNALS
        # =====================================================
        cur.execute("""
        CREATE TABLE IF NOT EXISTS scanner_signals_weekly (
            asset_type TEXT NOT NULL,
            scanner_type TEXT NOT NULL,
            symbol_id INTEGER NOT NULL,
            signal_date DATE NOT NULL,

            breakout_high REAL,
            breakout_close REAL,
            current_close REAL,

            rsi_3 REAL,
            rsi_9 REAL,
            ema_rsi_9_3 REAL,
            wma_rsi_9_21 REAL,

            is_triggered BOOLEAN DEFAULT FALSE,
            trigger_date DATE,

            PRIMARY KEY(asset_type, scanner_type, symbol_id, signal_date)
        );
        """)

        log("📦 Created scanner_signals_weekly table")

        # 🔥 Optimized pending scan
        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_sws_pending
        ON scanner_signals_weekly(asset_type, scanner_type, signal_date)
        WHERE is_triggered = FALSE;
        """)

        log("⚡ Created idx_sws_pending")

        # 🔥 Fast lookup / upsert support
        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_sws_lookup
        ON scanner_signals_weekly(asset_type, scanner_type, symbol_id, signal_date);
        """)

        log("⚡ Created idx_sws_lookup")

        # 🔥 Trigger update performance
        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_sws_trigger_scan
        ON scanner_signals_weekly(asset_type, scanner_type, is_triggered);
        """)

        log("⚡ Created idx_sws_trigger_scan")

        # =====================================================
        # UNIFIED SCANNER SIGNALS (1d / 1wk / 1mo)
        # =====================================================
        cur.execute("""
        CREATE TABLE IF NOT EXISTS scanner_signals (
            asset_type TEXT NOT NULL,
            scanner_type TEXT NOT NULL,
            scanner_freq TEXT NOT NULL,

            symbol_id INTEGER NOT NULL,
            signal_date DATE NOT NULL,

            breakout_high REAL,
            breakout_close REAL,
            current_close REAL,

            rsi_3 REAL,
            rsi_9 REAL,
            ema_rsi_9_3 REAL,
            wma_rsi_9_21 REAL,

            PRIMARY KEY (
                asset_type,
                scanner_type,
                scanner_freq,
                symbol_id,
                signal_date
            )
        );
        """)

        log("📦 Created scanner_signals table")

        # 🔥 Fast scanner queries
        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_ss_scan
        ON scanner_signals (
            asset_type,
            scanner_type,
            scanner_freq,
            signal_date DESC
        );
        """)

        log("⚡ Created idx_ss_scan")

        # 🔥 Fast symbol history lookups
        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_ss_symbol
        ON scanner_signals (
            symbol_id,
            signal_date DESC
        );
        """)

        log("⚡ Created idx_ss_symbol")

        log("✅ create_scanner_tables completed successfully")

    except Exception as e:
        log(f"🔥 ERROR in create_scanner_tables: {e}")
        raise