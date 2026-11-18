# database/equity/drop_tables.py

from config.logger import log

def drop_all_tables(cur, conn):
    tables = [
        "currency_master",
        "holidays_nse",
        "nse_india_index_constituents",
        "nse_india_index_srt",

        "yahoo_india_equity_symbols",
        "nse_india_index_symbols",
        "yahoo_usa_equity_symbols",
        "yahoo_global_index_symbols",
        "yahoo_commodity_symbols",
        "yahoo_crypto_symbols",
        "yahoo_forex_symbols",

        "yahoo_india_equity_price",
        "nse_india_index_price",
        "yahoo_usa_equity_price",
        "yahoo_global_index_price",
        "yahoo_commodity_price",
        "yahoo_crypto_price",
        "yahoo_forex_price",

        "yahoo_india_equity_indicators",
        "nse_india_index_indicators",
        "yahoo_usa_equity_indicators",
        "yahoo_global_index_indicators",
        "yahoo_commodity_indicators",
        "yahoo_crypto_indicators",
        "yahoo_forex_indicators",

        "scanner_signals_weekly",
        "nse_vix_features",

        "yahoo_india_equity_smc_structure",
        "yahoo_india_equity_smc_swings",
        "yahoo_india_equity_smc_order_blocks",
        "yahoo_india_equity_smc_fvg",
        "yahoo_india_equity_smc_equal_levels",
        "yahoo_india_equity_smc_snapshot",
    ]

    for t in tables:
        cur.execute(f"DROP TABLE IF EXISTS {t} CASCADE;")

    conn.commit()
    log("DROP COMPLETE")