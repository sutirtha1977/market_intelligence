
# database/equity/symbols.py

from psycopg2 import sql
from config.logger import log


# =========================================================
# SYMBOL TABLE CONFIGURATION
# =========================================================

SYMBOL_TABLES = [
    "yahoo_india_equity_symbols",
    "yahoo_india_index_symbols",
    "nse_india_index_symbols",
    "yahoo_usa_equity_symbols",
    "yahoo_global_index_symbols",
    "yahoo_commodity_symbols",
    "yahoo_crypto_symbols",
    "yahoo_forex_symbols",
]


# =========================================================
# CREATE / UPDATE SYMBOL TABLE
# =========================================================

def create_symbol_table(cur, table):

    table_id = sql.Identifier(table)

    # -----------------------------------------------------
    # CREATE TABLE
    # -----------------------------------------------------

    cur.execute(
        sql.SQL("""
            CREATE TABLE IF NOT EXISTS {} (
                symbol_id SERIAL PRIMARY KEY,
                name TEXT,
                symbol TEXT,
                exchange TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                is_future BOOLEAN DEFAULT FALSE,

                CONSTRAINT {} UNIQUE (symbol, exchange)
            );
        """).format(
            table_id,
            sql.Identifier(f"uq_{table}_symbol_exchange")
        )
    )

    # -----------------------------------------------------
    # ADD MISSING COLUMNS
    # -----------------------------------------------------

    cur.execute(
        sql.SQL("""
            ALTER TABLE {}
                ADD COLUMN IF NOT EXISTS name TEXT,
                ADD COLUMN IF NOT EXISTS symbol TEXT,
                ADD COLUMN IF NOT EXISTS exchange TEXT,
                ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE,
                ADD COLUMN IF NOT EXISTS is_future BOOLEAN DEFAULT FALSE;
        """).format(table_id)
    )

    # -----------------------------------------------------
    # INDEX: EXCHANGE
    # -----------------------------------------------------

    cur.execute(
        sql.SQL("""
            CREATE INDEX IF NOT EXISTS {}
            ON {} (exchange);
        """).format(
            sql.Identifier(f"idx_{table}_exchange"),
            table_id
        )
    )

    # -----------------------------------------------------
    # PARTIAL INDEX: ACTIVE SYMBOLS BY EXCHANGE
    # -----------------------------------------------------

    cur.execute(
        sql.SQL("""
            CREATE INDEX IF NOT EXISTS {}
            ON {} (exchange)
            WHERE is_active = TRUE;
        """).format(
            sql.Identifier(f"idx_{table}_active_exchange"),
            table_id
        )
    )


# =========================================================
# CREATE ALL SYMBOL TABLES
# =========================================================

def create_symbol_tables(cur):

    try:

        log("========== SYMBOL TABLE SETUP START ==========")

        for table in SYMBOL_TABLES:

            try:

                log(f"📦 Creating symbol table: {table}")

                create_symbol_table(cur, table)

                log(f"✅ Symbol table ready: {table}")

            except Exception as e:

                log(f"❌ Failed creating symbol table {table}: {e}")
                raise

        log("🚀 All symbol tables created successfully")

    except Exception as e:

        log(f"🔥 ERROR in create_symbol_tables: {e}")
        raise
