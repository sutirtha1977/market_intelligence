# database/equity/vcp_tables.py

from config.logger import log

def create_vcp_tables(cur):

    try:

        configs = [
            ("yahoo_india_equity","yahoo_india_equity_symbols"),
            ("yahoo_usa_equity","yahoo_usa_equity_symbols"),
            ("yahoo_global_index","yahoo_global_index_symbols"),
            ("yahoo_india_index","yahoo_india_index_symbols"),
            ("yahoo_commodity","yahoo_commodity_symbols"),
            ("yahoo_crypto","yahoo_crypto_symbols"),
            ("yahoo_forex","yahoo_forex_symbols"),
            ("nse_india_index","nse_india_index_symbols"),
        ]

        for asset, sym in configs:

            log(f"📦 Creating VCP tables for: {asset}")

            # =========================================================
            # TABLE NAMES
            # =========================================================
            pivots = f"{asset}_vcp_pivots"
            contractions = f"{asset}_vcp_contractions"
            patterns = f"{asset}_vcp_patterns"
            signals = f"{asset}_vcp_signals"

            # =========================================================
            # 1. PIVOTS
            # =========================================================
            cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {pivots} (
                symbol_id INT NOT NULL,
                timeframe TEXT NOT NULL,
                date DATE NOT NULL,

                pivot_type CHAR(1) NOT NULL CHECK (pivot_type IN ('H','L')),
                price REAL NOT NULL,

                left_bars INT DEFAULT 3,
                right_bars INT DEFAULT 3,

                created_at TIMESTAMP DEFAULT NOW(),

                PRIMARY KEY (symbol_id, timeframe, date, pivot_type)
            );
            """)

            cur.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_{pivots}_lookup
            ON {pivots}(symbol_id, timeframe, date);
            """)

            # =========================================================
            # 2. CONTRACTIONS
            # =========================================================
            cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {contractions} (
                contraction_id SERIAL PRIMARY KEY,

                symbol_id INT NOT NULL,
                timeframe TEXT NOT NULL,

                high_date DATE NOT NULL,
                high_price REAL NOT NULL,

                low_date DATE NOT NULL,
                low_price REAL NOT NULL,

                contraction_pct REAL,
                duration_days INT,
                avg_volume REAL,

                created_at TIMESTAMP DEFAULT NOW()
            );
            """)

            cur.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_{contractions}_lookup
            ON {contractions}(symbol_id, timeframe);
            """)

            # =========================================================
            # 3. PATTERNS
            # =========================================================
            cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {patterns} (
                pattern_id SERIAL PRIMARY KEY,

                symbol_id INT NOT NULL,
                timeframe TEXT NOT NULL,

                start_date DATE,
                end_date DATE,

                num_contractions INT,

                contraction_1 REAL,
                contraction_2 REAL,
                contraction_3 REAL,

                range_tightening BOOLEAN,
                volume_contracting BOOLEAN,
                is_valid BOOLEAN,

                resistance_level REAL,
                pivot_price REAL,

                created_at TIMESTAMP DEFAULT NOW()
            );
            """)

            cur.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_{patterns}_lookup
            ON {patterns}(symbol_id, timeframe);
            """)

            # =========================================================
            # 4. SIGNALS
            # =========================================================
            cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {signals} (
                signal_id SERIAL PRIMARY KEY,

                pattern_id INT,

                symbol_id INT NOT NULL,
                timeframe TEXT NOT NULL,
                date DATE NOT NULL,

                breakout_price REAL,
                breakout_volume REAL,
                volume_ratio REAL,

                signal_type TEXT DEFAULT 'BREAKOUT',
                is_triggered BOOLEAN DEFAULT FALSE,

                created_at TIMESTAMP DEFAULT NOW()
            );
            """)

            cur.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_{signals}_lookup
            ON {signals}(symbol_id, timeframe, date);
            """)

            cur.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_{signals}_pattern
            ON {signals}(pattern_id);
            """)

            log(f"✅ Done VCP tables for: {asset}")

        log("🚀 All VCP tables created successfully")

    except Exception as e:
        log(f"🔥 ERROR in create_vcp_tables: {e}")
        raise