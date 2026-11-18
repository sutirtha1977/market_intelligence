# database/equity/symbols.py

from config.logger import log

def create_symbol_tables(cur):

    try:

        def create_symbol_table(table):
            cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {table} (
                symbol_id SERIAL PRIMARY KEY,
                name TEXT,
                symbol TEXT,
                exchange TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                is_future BOOLEAN DEFAULT FALSE,
                UNIQUE(symbol, exchange)
            );
            """)

            # 🔥 PRODUCTION INDEXES
            cur.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_{table}_symbol
            ON {table}(symbol);
            """)

            cur.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_{table}_exchange
            ON {table}(exchange);
            """)

            cur.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_{table}_active
            ON {table}(is_active);
            """)

            cur.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_{table}_symbol_exchange
            ON {table}(symbol, exchange);
            """)

        symbol_tables = [
            "yahoo_india_equity_symbols",
            "yahoo_india_index_symbols",
            "nse_india_index_symbols",
            "yahoo_usa_equity_symbols",
            "yahoo_global_index_symbols",
            "yahoo_commodity_symbols",
            "yahoo_crypto_symbols",
            "yahoo_forex_symbols",
        ]

        for table in symbol_tables:
            log(f"📦 Creating symbol table: {table}")
            create_symbol_table(table)
            log(f"✅ Done: {table}")

        log("🚀 Symbol tables created successfully")

    except Exception as e:
        log(f"🔥 ERROR in create_symbol_tables: {e}")
        raise