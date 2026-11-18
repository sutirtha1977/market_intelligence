# database/equity/indicators.py

from config.logger import log

def create_indicator_tables(cur):

    try:
        log("🚀 Creating indicator tables...")

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

        for p, sym in configs:
            table = f"{p}_indicators"

            cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {table} (
                symbol_id INTEGER,
                timeframe TEXT,
                date DATE,

                ema_3 REAL DEFAULT 0,
                ema_5 REAL DEFAULT 0,
                ema_7 REAL DEFAULT 0,
                ema_9 REAL DEFAULT 0,
                ema_10 REAL DEFAULT 0,

                sma_20 REAL DEFAULT 0,
                sma_50 REAL DEFAULT 0,
                sma_100 REAL DEFAULT 0,
                sma_200 REAL DEFAULT 0,

                sma_10_vol REAL DEFAULT 0,
                sma_20_vol REAL DEFAULT 0,

                rsi_3 REAL DEFAULT 0,
                rsi_9 REAL DEFAULT 0,
                rsi_14 REAL DEFAULT 0,
                rsi_10_ema_21 REAL DEFAULT 0,
                ema_rsi_9_3 REAL DEFAULT 0,
                ema_rsi_9_5 REAL DEFAULT 0,
                wma_rsi_9_21 REAL DEFAULT 0,

                macd REAL DEFAULT 0,
                macd_signal REAL DEFAULT 0,

                bb_upper REAL DEFAULT 0,
                bb_middle REAL DEFAULT 0,
                bb_lower REAL DEFAULT 0,

                rs REAL,
                rs_ma REAL,
                rs_slope REAL,
                rs_ma_rising BOOLEAN,
                rs_ma_falling BOOLEAN,

                PRIMARY KEY(symbol_id, timeframe, date),
                FOREIGN KEY(symbol_id) REFERENCES {sym}(symbol_id) ON DELETE CASCADE
            );
            """)

            # 🔥 MATCH PRICE INDEX STRATEGY
            cur.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_{table}_sym_tf_date_desc 
                ON {table}(symbol_id, timeframe, date DESC);
            """)

            cur.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_{table}_date_brin 
                ON {table} USING BRIN(date);
            """)

            # 🔥 FIXED (removed rs_rank because it does not exist)
            cur.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_{table}_tf_date_rs 
                ON {table}(timeframe, date, rs DESC);
            """)

        log("✅ Indicator tables created successfully")

    except Exception as e:
        log(f"❌ ERROR creating indicator tables: {e}")
        raise