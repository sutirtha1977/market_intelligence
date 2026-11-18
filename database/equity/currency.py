# database/equity/currency.py

from config.logger import log

def create_currency_master(cur):
    try:
        log("🚀 Creating currency_master table")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS currency_master (
                currency_code CHAR(3) PRIMARY KEY,
                currency_name TEXT NOT NULL
            );
        """)

        data = {
            "USD":"US Dollar","EUR":"Euro","INR":"Indian Rupee","GBP":"British Pound",
            "JPY":"Japanese Yen","AUD":"Australian Dollar","CAD":"Canadian Dollar",
            "CHF":"Swiss Franc","CNY":"Chinese Yuan","HKD":"Hong Kong Dollar",
            "SGD":"Singapore Dollar","MXN":"Mexican Peso","BRL":"Brazilian Real",
            "ZAR":"South African Rand","TRY":"Turkish Lira","NZD":"New Zealand Dollar"
        }

        for c, n in data.items():
            cur.execute("""
                INSERT INTO currency_master VALUES (%s,%s)
                ON CONFLICT DO NOTHING
            """, (c, n))

        log(f"✅ currency_master inserted {len(data)} records")

    except Exception as e:
        log(f"❌ ERROR creating currency_master: {e}")
        raise