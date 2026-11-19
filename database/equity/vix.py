
# database/equity/vix.py

from config.logger import log


# =========================================================
# CREATE NSE VIX FEATURES TABLE
# =========================================================

def create_vix_table(cur):

    try:

        log("========== NSE VIX TABLE SETUP START ==========")

        # -------------------------------------------------
        # CREATE TABLE
        # -------------------------------------------------

        cur.execute("""
            CREATE TABLE IF NOT EXISTS nse_vix_features (

                date DATE PRIMARY KEY,

                vix DOUBLE PRECISION NOT NULL,

                vix_ma_5 DOUBLE PRECISION,
                vix_ma_10 DOUBLE PRECISION,

                vix_change DOUBLE PRECISION,
                vix_percentile DOUBLE PRECISION,

                vix_regime TEXT,
                vix_signal TEXT,

                created_at TIMESTAMPTZ NOT NULL
                    DEFAULT CURRENT_TIMESTAMP

            );
        """)

        log("📦 nse_vix_features table ready")

        # -------------------------------------------------
        # REGIME INDEX
        # -------------------------------------------------

        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_vix_regime
            ON nse_vix_features(vix_regime);
        """)

        log("⚡ VIX regime index ready")

        # -------------------------------------------------
        # SIGNAL INDEX
        # -------------------------------------------------

        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_vix_signal
            ON nse_vix_features(vix_signal);
        """)

        log("⚡ VIX signal index ready")

        log("🚀 NSE VIX table setup completed successfully")

    except Exception as e:

        log(f"🔥 ERROR creating NSE VIX table: {e}")
        raise
