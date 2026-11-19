
# database/equity/indicators.py

from psycopg2 import sql
from config.logger import log


# =========================================================
# INDICATOR TABLE CONFIGURATION
# =========================================================

INDICATOR_TABLES = [
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
# INDICATOR COLUMN DEFINITIONS
# =========================================================

INDICATOR_COLUMNS = {
    "ema_3": "DOUBLE PRECISION DEFAULT 0",
    "ema_5": "DOUBLE PRECISION DEFAULT 0",
    "ema_7": "DOUBLE PRECISION DEFAULT 0",
    "ema_9": "DOUBLE PRECISION DEFAULT 0",
    "ema_10": "DOUBLE PRECISION DEFAULT 0",

    "sma_20": "DOUBLE PRECISION DEFAULT 0",
    "sma_50": "DOUBLE PRECISION DEFAULT 0",
    "sma_100": "DOUBLE PRECISION DEFAULT 0",
    "sma_200": "DOUBLE PRECISION DEFAULT 0",

    "sma_10_vol": "DOUBLE PRECISION DEFAULT 0",
    "sma_20_vol": "DOUBLE PRECISION DEFAULT 0",

    "rsi_3": "DOUBLE PRECISION DEFAULT 0",
    "rsi_9": "DOUBLE PRECISION DEFAULT 0",
    "rsi_14": "DOUBLE PRECISION DEFAULT 0",
    "rsi_10_ema_21": "DOUBLE PRECISION DEFAULT 0",

    "ema_rsi_9_3": "DOUBLE PRECISION DEFAULT 0",
    "ema_rsi_9_5": "DOUBLE PRECISION DEFAULT 0",
    "wma_rsi_9_21": "DOUBLE PRECISION DEFAULT 0",

    "macd": "DOUBLE PRECISION DEFAULT 0",
    "macd_signal": "DOUBLE PRECISION DEFAULT 0",

    "bb_upper": "DOUBLE PRECISION DEFAULT 0",
    "bb_middle": "DOUBLE PRECISION DEFAULT 0",
    "bb_lower": "DOUBLE PRECISION DEFAULT 0",

    "rs": "DOUBLE PRECISION",
    "rs_ma": "DOUBLE PRECISION",
    "rs_slope": "DOUBLE PRECISION",

    "rs_ma_rising": "BOOLEAN",
    "rs_ma_falling": "BOOLEAN",
}


# =========================================================
# CREATE INDIVIDUAL INDICATOR TABLE
# =========================================================

def create_indicator_table(cur, prefix, symbol_table):

    table = f"{prefix}_indicators"

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

                ema_3 DOUBLE PRECISION DEFAULT 0,
                ema_5 DOUBLE PRECISION DEFAULT 0,
                ema_7 DOUBLE PRECISION DEFAULT 0,
                ema_9 DOUBLE PRECISION DEFAULT 0,
                ema_10 DOUBLE PRECISION DEFAULT 0,

                sma_20 DOUBLE PRECISION DEFAULT 0,
                sma_50 DOUBLE PRECISION DEFAULT 0,
                sma_100 DOUBLE PRECISION DEFAULT 0,
                sma_200 DOUBLE PRECISION DEFAULT 0,

                sma_10_vol DOUBLE PRECISION DEFAULT 0,
                sma_20_vol DOUBLE PRECISION DEFAULT 0,

                rsi_3 DOUBLE PRECISION DEFAULT 0,
                rsi_9 DOUBLE PRECISION DEFAULT 0,
                rsi_14 DOUBLE PRECISION DEFAULT 0,
                rsi_10_ema_21 DOUBLE PRECISION DEFAULT 0,

                ema_rsi_9_3 DOUBLE PRECISION DEFAULT 0,
                ema_rsi_9_5 DOUBLE PRECISION DEFAULT 0,
                wma_rsi_9_21 DOUBLE PRECISION DEFAULT 0,

                macd DOUBLE PRECISION DEFAULT 0,
                macd_signal DOUBLE PRECISION DEFAULT 0,

                bb_upper DOUBLE PRECISION DEFAULT 0,
                bb_middle DOUBLE PRECISION DEFAULT 0,
                bb_lower DOUBLE PRECISION DEFAULT 0,

                rs DOUBLE PRECISION,
                rs_ma DOUBLE PRECISION,
                rs_slope DOUBLE PRECISION,

                rs_ma_rising BOOLEAN,
                rs_ma_falling BOOLEAN,

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

    add_columns = sql.SQL(", ").join(
        sql.SQL("ADD COLUMN IF NOT EXISTS {} {}").format(
            sql.Identifier(column),
            sql.SQL(definition)
        )
        for column, definition in INDICATOR_COLUMNS.items()
    )

    cur.execute(
        sql.SQL("ALTER TABLE {} {}").format(
            table_id,
            add_columns
        )
    )

    # -----------------------------------------------------
    # ENSURE DEFAULT VALUES
    # -----------------------------------------------------

    default_columns = [
        column
        for column, definition in INDICATOR_COLUMNS.items()
        if "DEFAULT 0" in definition
    ]

    alter_defaults = sql.SQL(", ").join(
        sql.SQL("ALTER COLUMN {} SET DEFAULT 0").format(
            sql.Identifier(column)
        )
        for column in default_columns
    )

    cur.execute(
        sql.SQL("ALTER TABLE {} {}").format(
            table_id,
            alter_defaults
        )
    )

    # -----------------------------------------------------
    # RELATIVE STRENGTH INDEX
    # -----------------------------------------------------

    cur.execute(
        sql.SQL("""
            CREATE INDEX IF NOT EXISTS {}
            ON {} (timeframe, date, rs DESC);
        """).format(
            sql.Identifier(f"idx_{table}_tf_date_rs"),
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
# CREATE ALL INDICATOR TABLES
# =========================================================

def create_indicator_tables(cur):

    try:

        log("========== INDICATOR TABLE SETUP START ==========")

        for prefix, symbol_table in INDICATOR_TABLES:

            table = f"{prefix}_indicators"

            try:

                log(f"📦 Creating indicator table: {table}")

                create_indicator_table(
                    cur,
                    prefix,
                    symbol_table
                )

                log(f"✅ Indicator table ready: {table}")

            except Exception as e:

                log(f"❌ Failed creating indicator table {table}: {e}")
                raise

        log("🚀 All indicator tables created successfully")

    except Exception as e:

        log(f"🔥 ERROR creating indicator tables: {e}")
        raise
