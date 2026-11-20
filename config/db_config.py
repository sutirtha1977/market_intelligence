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
    ("YAHOO_INDIA_EQUITY", "yahoo_india_equity_symbols", ["symbol","name","series","exchange"]),
    ("YAHOO_USA_EQUITY",   "yahoo_usa_equity_symbols",   ["symbol","name","series","exchange"]),
    ("YAHOO_GLOBAL_INDEX", "yahoo_global_index_symbols", ["symbol","name","series","exchange"]),
    ("YAHOO_INDIA_INDEX", "yahoo_india_index_symbols",   ["symbol","name","series","exchange"]),
    ("YAHOO_COMMODITY",    "yahoo_commodity_symbols",    ["symbol","name","series","exchange"]),
    ("YAHOO_CRYPTO",       "yahoo_crypto_symbols",       ["symbol","name","series","exchange"]),
    ("YAHOO_FOREX",        "yahoo_forex_symbols",        ["symbol","name","series","exchange"]),
    ("NSE_INDIA_INDEX",    "nse_india_index_symbols",    ["symbol","name","series","exchange"]),
]
# ----------------------------------------------------------------------------------------------
ASSET_TABLE_CONFIG = {
    # -------------------------------
    # INDIA EQUITY
    # -------------------------------
    "yahoo_india_equity": {
        "symbol": "yahoo_india_equity_symbols",
        "price": "yahoo_india_equity_price",
        "indicator": "yahoo_india_equity_indicators",
        "vcp": {
            "pivot": "yahoo_india_equity_vcp_pivots",
            "contraction": "yahoo_india_equity_vcp_contractions",
            "pattern": "yahoo_india_equity_vcp_patterns",
            "signal": "yahoo_india_equity_vcp_signals",
        }
    },
    # -------------------------------
    # USA EQUITY
    # -------------------------------
    "yahoo_usa_equity": {
        "symbol": "yahoo_usa_equity_symbols",
        "price": "yahoo_usa_equity_price",
        "indicator": "yahoo_usa_equity_indicators",
        "vcp": {
            "pivot": "yahoo_usa_equity_vcp_pivots",
            "contraction": "yahoo_usa_equity_vcp_contractions",
            "pattern": "yahoo_usa_equity_vcp_patterns",
            "signal": "yahoo_usa_equity_vcp_signals",
        }
    },
    # -------------------------------
    # INDEXES
    # -------------------------------
    "nse_india_index": {
        "symbol": "nse_india_index_symbols",
        "price": "nse_india_index_price",
        "indicator": "nse_india_index_indicators",
        "constituents": "nse_india_index_constituents",
        "srt": "nse_india_index_srt",
        "vix": "nse_vix_features",
        "vcp": {
            "pivot": "nse_india_index_vcp_pivots",
            "contraction": "nse_india_index_vcp_contractions",
            "pattern": "nse_india_index_vcp_patterns",
            "signal": "nse_india_index_vcp_signals",
        }
    },
    "yahoo_india_index": {
        "symbol": "yahoo_india_index_symbols",
        "price": "yahoo_india_index_price",
        "indicator": "yahoo_india_index_indicators",
        "vcp": {
            "pivot": "yahoo_india_index_vcp_pivots",
            "contraction": "yahoo_india_index_vcp_contractions",
            "pattern": "yahoo_india_index_vcp_patterns",
            "signal": "yahoo_india_index_vcp_signals",
        }
    },
    "yahoo_global_index": {
        "symbol": "yahoo_global_index_symbols",
        "price": "yahoo_global_index_price",
        "indicator": "yahoo_global_index_indicators",
        "vcp": {
            "pivot": "yahoo_global_index_vcp_pivots",
            "contraction": "yahoo_global_index_vcp_contractions",
            "pattern": "yahoo_global_index_vcp_patterns",
            "signal": "yahoo_global_index_vcp_signals",
        }
    },
    # -------------------------------
    # OTHER ASSETS
    # -------------------------------
    "yahoo_commodity": {
        "symbol": "yahoo_commodity_symbols",
        "price": "yahoo_commodity_price",
        "indicator": "yahoo_commodity_indicators",
        "vcp": {
            "pivot": "yahoo_commodity_vcp_pivots",
            "contraction": "yahoo_commodity_vcp_contractions",
            "pattern": "yahoo_commodity_vcp_patterns",
            "signal": "yahoo_commodity_vcp_signals",
        }
    },
    "yahoo_crypto": {
        "symbol": "yahoo_crypto_symbols",
        "price": "yahoo_crypto_price",
        "indicator": "yahoo_crypto_indicators",
        "vcp": {
            "pivot": "yahoo_crypto_vcp_pivots",
            "contraction": "yahoo_crypto_vcp_contractions",
            "pattern": "yahoo_crypto_vcp_patterns",
            "signal": "yahoo_crypto_vcp_signals",
        }
    },
    "yahoo_forex": {
        "symbol": "yahoo_forex_symbols",
        "price": "yahoo_forex_price",
        "indicator": "yahoo_forex_indicators",
        "vcp": {
            "pivot": "yahoo_forex_vcp_pivots",
            "contraction": "yahoo_forex_vcp_contractions",
            "pattern": "yahoo_forex_vcp_patterns",
            "signal": "yahoo_forex_vcp_signals",
        }
    },
    # -------------------------------
    # SCANNERS
    # -------------------------------
    "scanner": {
        "weekly": "scanner_signals_weekly",
        "signals": "scanner_signals",
        "momentum": "scanner_signals_momentum",
    },
    # -------------------------------
    # REFERENCE
    # -------------------------------
    "reference": {
        "currency_master": "currency_master",
        "nse_holidays": "nse_holidays"
    }
}