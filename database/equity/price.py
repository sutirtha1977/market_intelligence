
# database/equity/price.py

from psycopg2 import sql
from config.logger import log


# =========================================================
# PRICE TABLE CONFIGURATION
# =========================================================

PRICE_TABLES = [
    ("yahoo_india_equity", "yahoo_india_equity_symbols"),
    ("yahoo_usa_equity", "yahoo_usa_equity_symbols"),
    ("yahoo_global_index", "yahoo_global_index_symbols"),
    ("yahoo_india_index", "yahoo_india_index_symbols"),
    ("yahoo_commodity", "yahoo_commodity_symbols"),
    ("yahoo_crypto", "yahoo_crypto_symbols"),
    ("yahoo_forex", "yahoo_forex_symbols"),
    ("nse_india_index", "nse_india_index_symbols"),
]


# =========================================================
# CREATE INDIVIDUAL PRICE TABLE
# =========================================================

def create_price_table(cur, prefix, symbol_table):

    table = f"{prefix}_price"

    table_id = sql.Identifier(table)
    symbol_table_id = sql.Identifier(symbol_table)

    # -----------------------------------------------------
    # CREATE TABLE
    # -----------------------------------------------------

    cur.execute(
        sql.SQL("""
            CREATE TABLE IF NOT EXISTS {} (

                symbol_id INTEGER NOT NULL,
                timeframe TEXT NOT NULL,
                date DATE NOT NULL,

                open DOUBLE PRECISION DEFAULT 0,
                high DOUBLE PRECISION DEFAULT 0,
                low DOUBLE PRECISION DEFAULT 0,
                close DOUBLE PRECISION DEFAULT 0,
                adj_close DOUBLE PRECISION DEFAULT 0,

                volume BIGINT DEFAULT 0,

                delv_pct DOUBLE PRECISION DEFAULT 0,
                pct_price_change DOUBLE PRECISION DEFAULT 0,

                PRIMARY KEY (symbol_id, timeframe, date),

                FOREIGN KEY (symbol_id)
                    REFERENCES {} (symbol_id)
                    ON DELETE CASCADE

            );
        """).format(
            table_id,
            symbol_table_id
        )
    )

    # -----------------------------------------------------
    # ADD MISSING COLUMNS TO EXISTING TABLES
    # -----------------------------------------------------

    cur.execute(
        sql.SQL("""
            ALTER TABLE {}
                ADD COLUMN IF NOT EXISTS open
                    DOUBLE PRECISION DEFAULT 0,

                ADD COLUMN IF NOT EXISTS high
                    DOUBLE PRECISION DEFAULT 0,

                ADD COLUMN IF NOT EXISTS low
                    DOUBLE PRECISION DEFAULT 0,

                ADD COLUMN IF NOT EXISTS close
                    DOUBLE PRECISION DEFAULT 0,

                ADD COLUMN IF NOT EXISTS adj_close
                    DOUBLE PRECISION DEFAULT 0,

                ADD COLUMN IF NOT EXISTS volume
                    BIGINT DEFAULT 0,

                ADD COLUMN IF NOT EXISTS delv_pct
                    DOUBLE PRECISION DEFAULT 0,

                ADD COLUMN IF NOT EXISTS pct_price_change
                    DOUBLE PRECISION DEFAULT 0;
        """).format(table_id)
    )

    # -----------------------------------------------------
    # ENSURE DEFAULT VALUES ON EXISTING COLUMNS
    # -----------------------------------------------------

    cur.execute(
        sql.SQL("""
            ALTER TABLE {}
                ALTER COLUMN open SET DEFAULT 0,
                ALTER COLUMN high SET DEFAULT 0,
                ALTER COLUMN low SET DEFAULT 0,
                ALTER COLUMN close SET DEFAULT 0,
                ALTER COLUMN adj_close SET DEFAULT 0,
                ALTER COLUMN volume SET DEFAULT 0,
                ALTER COLUMN delv_pct SET DEFAULT 0,
                ALTER COLUMN pct_price_change SET DEFAULT 0;
        """).format(table_id)
    )

    # -----------------------------------------------------
    # MARKET-WIDE TIMEFRAME / DATE INDEX
    # -----------------------------------------------------

    cur.execute(
        sql.SQL("""
            CREATE INDEX IF NOT EXISTS {}
            ON {} (timeframe, date DESC);
        """).format(
            sql.Identifier(f"idx_{table}_tf_date"),
            table_id
        )
    )

    # -----------------------------------------------------
    # BRIN DATE INDEX
    # -----------------------------------------------------

    cur.execute(
        sql.SQL("""
            CREATE INDEX IF NOT EXISTS {}
            ON {} USING BRIN (date);
        """).format(
            sql.Identifier(f"idx_{table}_date_brin"),
            table_id
        )
    )


# =========================================================
# CREATE ALL PRICE TABLES
# =========================================================

def create_price_tables(cur):

    try:

        log("========== PRICE TABLE SETUP START ==========")

        for prefix, symbol_table in PRICE_TABLES:

            table = f"{prefix}_price"

            try:

                log(f"📦 Creating price table: {table}")

                create_price_table(
                    cur,
                    prefix,
                    symbol_table
                )

                log(f"✅ Price table ready: {table}")

            except Exception as e:

                log(f"❌ Failed creating price table {table}: {e}")
                raise

        log("🚀 All price tables created successfully")

    except Exception as e:

        log(f"🔥 ERROR in create_price_tables: {e}")
        raise
