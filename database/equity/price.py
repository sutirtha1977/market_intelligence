# database/equity/price.py

from config.logger import log

def create_price_tables(cur):

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

        for p, sym in configs:
            table = f"{p}_price"

            log(f"📦 Creating table: {table}")

            cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {table} (
                symbol_id INTEGER,
                timeframe TEXT,
                date DATE,
                open REAL DEFAULT 0,
                high REAL DEFAULT 0,
                low REAL DEFAULT 0,
                close REAL DEFAULT 0,
                adj_close REAL DEFAULT 0,
                volume REAL DEFAULT 0,
                delv_pct REAL DEFAULT 0,
                pct_price_change REAL DEFAULT 0,
                PRIMARY KEY(symbol_id, timeframe, date),
                FOREIGN KEY(symbol_id) REFERENCES {sym}(symbol_id) ON DELETE CASCADE
            );
            """)

            # 🔥 PRODUCTION INDEXES
            cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{table}_sym_tf_date_desc ON {table}(symbol_id, timeframe, date DESC);")
            cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{table}_tf_date ON {table}(timeframe, date DESC);")
            cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{table}_date_brin ON {table} USING BRIN(date);")

            log(f"✅ Done table + indexes: {table}")

    except Exception as e:
        log(f"🔥 ERROR in create_price_tables: {e}")
        raise