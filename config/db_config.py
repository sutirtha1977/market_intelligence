# config/db_table.py

DB_CONFIG = {
    "host": "localhost",
    "dbname": "market_intelligence",
    "user": "sutirtha",
    "password": "1977",
    "port": 5432
}
# ----------------------------------------------------------------------------------------------
PG_CONN_STR = "postgresql+psycopg2://sutirtha:1977@localhost:5432/market_intelligence"
# ----------------------------------------------------------------------------------------------
ASSET_CHOICE_MAP = {
    "INDIA Equity": "yahoo_india_equity",
    "INDIA Index": "yahoo_india_index",
    "USA Equity": "yahoo_usa_equity",
    "GLOBAL Index": "yahoo_global_index",
    "Commodity": "yahoo_commodity",
    "Crypto": "yahoo_crypto",
    "Forex": "yahoo_forex",
}
# ----------------------------------------------------------------------------------------------
SYMBOL_MAPPING = [
    ("YAHOO_INDIA_EQUITY", "yahoo_india_equity_symbols", ["name", "symbol", "exchange"]),
    ("YAHOO_USA_EQUITY",   "yahoo_usa_equity_symbols",   ["name", "symbol", "exchange"]),
    ("YAHOO_GLOBAL_INDEX", "yahoo_global_index_symbols", ["name", "symbol", "exchange"]),
    ("YAHOO_INDIA_INDEX", "yahoo_india_index_symbols",   ["name", "symbol", "exchange"]),
    ("YAHOO_COMMODITY",    "yahoo_commodity_symbols",    ["name", "symbol", "exchange"]),
    ("YAHOO_CRYPTO",       "yahoo_crypto_symbols",       ["name", "symbol", "exchange"]),
    ("YAHOO_FOREX",        "yahoo_forex_symbols",        ["name", "symbol", "exchange"]),
    ("NSE_INDIA_INDEX",    "nse_india_index_symbols",    ["name", "symbol", "exchange"]),
]