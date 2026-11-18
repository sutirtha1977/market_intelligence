# database/equity/vix.py

from config.logger import log

def create_vix_table(cur):

    try:

        cur.execute("""
        CREATE TABLE IF NOT EXISTS nse_vix_features (
            date DATE NOT NULL,
            vix REAL NOT NULL,
            vix_ma_5 REAL,
            vix_ma_10 REAL,
            vix_change REAL,
            vix_percentile REAL,
            vix_regime TEXT,
            vix_signal TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT nse_vix_features_pkey PRIMARY KEY (date)
        );
        """)

        log("📦 Created nse_vix_features table")

        # 🔥 PRODUCTION INDEXES
        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_vix_date_desc
        ON nse_vix_features(date DESC);
        """)

        log("⚡ Created idx_vix_date_desc")

        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_vix_regime
        ON nse_vix_features(vix_regime);
        """)

        log("⚡ Created idx_vix_regime")

        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_vix_signal
        ON nse_vix_features(vix_signal);
        """)

        log("⚡ Created idx_vix_signal")

        # Optional but useful for range scans (huge tables)
        cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_vix_date_brin
        ON nse_vix_features USING BRIN(date);
        """)

        log("⚡ Created idx_vix_date_brin")

        log("✅ VIX table created successfully")

    except Exception as e:
        log(f"🔥 ERROR in create_vix_table: {e}")
        raise