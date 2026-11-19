
# database/equity/currency.py

from psycopg2.extras import execute_values
from config.logger import log


# =========================================================
# CURRENCY MASTER DATA
# =========================================================

CURRENCIES = [
    ("USD", "US Dollar"),
    ("EUR", "Euro"),
    ("INR", "Indian Rupee"),
    ("GBP", "British Pound"),
    ("JPY", "Japanese Yen"),
    ("AUD", "Australian Dollar"),
    ("CAD", "Canadian Dollar"),
    ("CHF", "Swiss Franc"),
    ("CNY", "Chinese Yuan"),
    ("HKD", "Hong Kong Dollar"),
    ("SGD", "Singapore Dollar"),
    ("MXN", "Mexican Peso"),
    ("BRL", "Brazilian Real"),
    ("ZAR", "South African Rand"),
    ("TRY", "Turkish Lira"),
    ("NZD", "New Zealand Dollar"),
]


# =========================================================
# CREATE CURRENCY MASTER
# =========================================================

def create_currency_master(cur):

    try:

        log("🚀 Creating currency_master table")

        # -------------------------------------------------
        # CREATE TABLE
        # -------------------------------------------------

        cur.execute("""
            CREATE TABLE IF NOT EXISTS currency_master (

                currency_code VARCHAR(3) PRIMARY KEY,

                currency_name TEXT NOT NULL

            );
        """)

        # -------------------------------------------------
        # BULK INSERT
        # -------------------------------------------------

        execute_values(
            cur,
            """
            INSERT INTO currency_master (
                currency_code,
                currency_name
            )
            VALUES %s
            ON CONFLICT (currency_code) DO NOTHING
            RETURNING currency_code;
            """,
            CURRENCIES,
            page_size=100
        )

        inserted_count = len(cur.fetchall())

        # -------------------------------------------------
        # LOGGING
        # -------------------------------------------------

        log(
            f"✅ currency_master ready | "
            f"Inserted: {inserted_count} | "
            f"Total configured: {len(CURRENCIES)}"
        )

    except Exception as e:

        log(f"❌ ERROR creating currency_master: {e}")
        raise
