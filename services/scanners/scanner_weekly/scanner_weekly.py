
# services/scanners/scanner_weekly/scanner_weekly.py

from datetime import date

import pandas as pd

from services.scanners.common.scanner_runner import run_scanner

from services.scanners.scanner_weekly.data_engine_weekly import data_logic
from services.scanners.scanner_weekly.logic_engine_weekly import scanner_logic
from services.scanners.scanner_weekly.display_engine_weekly import display_logic


def scanner_weekly(
    asset_type: str = "yahoo_india_equity",
    start_year: int | None = None,
    lookback_years: int = 5,
    scanner_name="weekly",
) -> pd.DataFrame:

    return run_scanner(
        asset_type=asset_type,
        scanner_name=scanner_name,
        data_func=data_logic,
        logic_func=scanner_logic,
        display_func=display_logic,
        start_year=start_year or date.today().year,
        lookback_years=lookback_years,
    )
