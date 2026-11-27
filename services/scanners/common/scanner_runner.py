
# services/scanners/common/scanner_runner.py

import os
from datetime import date
from typing import Callable

import pandas as pd

from config.logger import log
from config.paths import SCANNER_DIR
from services.equity.cleanup_service import delete_files_in_folder


def run_scanner(
    asset_type: str,
    scanner_name: str,
    data_func: Callable,
    logic_func: Callable,
    display_func: Callable,
    start_year: int | None = None,
    lookback_years: int = 5,
) -> pd.DataFrame:
    """
    Generic execution engine for all scanners.

    Flow:
        1. Prepare scanner output folder
        2. Clean previous CSV files
        3. Extract data year by year
        4. Apply scanner conditions
        5. Save yearly signals
        6. Format current-year signals for display

    Returns:
        Formatted current-year signals.
    """

    try:
        start_year = start_year or date.today().year

        base_folder = os.path.join(
            SCANNER_DIR,
            scanner_name,
            asset_type
        )
        os.makedirs(base_folder, exist_ok=True)

        # Remove previous scanner output
        delete_files_in_folder(base_folder)

        current_signals = pd.DataFrame()

        # --------------------------------------------------
        # YEARLY SCANNER EXECUTION
        # --------------------------------------------------
        for year in range(
            start_year,
            start_year - lookback_years,
            -1
        ):
            try:
                log(
                    f"🔍 Running scanner: "
                    f"{scanner_name} | Year: {year}"
                )

                # DATA EXTRACTION
                df = data_func(
                    asset_type,
                    f"{year}-01-01",
                    f"{year}-12-31"
                )

                if df is None or df.empty:
                    log(f"⚠️ No data for {year}")
                    continue

                # SCANNER CONDITIONS
                signals = logic_func(df, asset_type)

                if signals is None or signals.empty:
                    log(f"⚠️ No signals for {year}")
                    continue

                # SAVE YEARLY SIGNALS
                file_path = os.path.join(
                    base_folder,
                    f"{scanner_name.upper()}_{year}.csv"
                )

                signals.to_csv(file_path, index=False)

                log(
                    f"✅ Saved signals for {year} | "
                    f"rows={len(signals)}"
                )

                # KEEP CURRENT YEAR FOR UI
                if year == start_year:
                    current_signals = signals.copy()

            except Exception as e:
                log(
                    f"❌ Error processing "
                    f"{scanner_name} | Year: {year} | {e}"
                )
                continue

        # --------------------------------------------------
        # DISPLAY CURRENT YEAR SIGNALS
        # --------------------------------------------------
        if current_signals.empty:
            log(
                f"⚠️ No current-year signals: "
                f"{scanner_name}"
            )
            return pd.DataFrame()

        display_df = display_func(current_signals)

        log(
            f"🏁 Scanner completed: "
            f"{scanner_name}"
        )

        return display_df

    except Exception as e:
        log(
            f"🚨 Fatal scanner error: "
            f"{scanner_name} | {e}"
        )
        return pd.DataFrame()
