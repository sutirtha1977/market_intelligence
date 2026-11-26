import traceback
from datetime import datetime

from services.scanners.backtest_weekly.data_engine_weekly import data_logic
from services.scanners.backtest_weekly.logic_engine_weekly import scanner_logic
from services.scanners.scanners_final.update_signals import upsert_scanner_signals
from config.logger import log

# --------------------------------------------------------------------------
def update_scanner_weekly(
    asset_type: str = "yahoo_india_equity",
    scanner_type: str = "weekly"
) -> int:

    try:

        total_signals = 0
        current_year = datetime.now().year

        for year in range(2000, current_year + 1):

            start_date = f"{year}-01-01"
            end_date = f"{year}-12-31"

            log(
                f"Scanner start | {asset_type} | {scanner_type} | "
                f"{start_date} -> {end_date}",
                level="INFO"
            )

            df_range = data_logic(
                asset_type,
                start_date,
                end_date
            )

            log(f"Data fetched | rows={len(df_range)}", level="DEBUG")

            if df_range.empty:
                log(f"No data found for year {year}", level="INFO")
                continue

            df = scanner_logic(df_range, asset_type)

            log(f"Signals after logic | rows={len(df)}", level="DEBUG")

            if df.empty:
                log(f"No signals found for year {year}", level="INFO")
                continue

            upsert_scanner_signals(
                df,
                asset_type,
                scanner_type,
                scanner_freq="1wk"
            )

            total_signals += len(df)

            log(
                f"Year completed | {year} | signals={len(df)}",
                level="INFO"
            )

        log(
            f"Scanner completed | total_signals={total_signals}",
            level="INFO"
        )

        return total_signals

    except Exception as e:
        log(
            f"Scanner failed | {asset_type} | "
            f"{scanner_type} | error={e}",
            level="ERROR"
        )
        log(traceback.format_exc(), level="ERROR")
        return 0

# --------------------------------------------------------------------------