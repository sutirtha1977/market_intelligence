import os
import pandas as pd

from datetime import date

from config.paths import SCANNER_DIR
from config.logger import log

from services.equity.cleanup_service import delete_files_in_folder

from services.scanners.backtest_future_breakdown.data_engine_future_breakdown import data_logic
from services.scanners.backtest_future_breakdown.logic_engine_future_breakdown import scanner_logic
from services.scanners.backtest_future_breakdown.display_engine_future_breakdown import display_logic

# --------------------------------------------------------------------------
def scanner_backtest_future_breakdown(
    asset_type: str = "yahoo_india_equity",
    start_year: int = date.today().year,
    lookback_years: int = 5,
    scanner_name: str = "future_breakdown"
) -> pd.DataFrame:

    try:

        base_folder = os.path.join(
            SCANNER_DIR,
            scanner_name,
            asset_type
        )
        os.makedirs(base_folder, exist_ok=True)
        delete_files_in_folder(base_folder)

        current_year = []

        for yr in range(
            start_year,
            start_year - lookback_years,
            -1
        ):
            try:
                log(
                    f"🔍 Running scanner: "
                    f"{scanner_name} | Year: {yr}"
                )
                df = data_logic(yr)
                if df is None or df.empty:
                    log(
                        f"⚠️ No data for {yr}"
                    )
                    continue
                signals = scanner_logic(df)
                if signals is None or signals.empty:
                    log(
                        f"⚠️ No signals for {yr}"
                    )
                    continue
                file_path = os.path.join(
                    base_folder,
                    f"{scanner_name.upper()}_{yr}.csv"
                )
                signals.to_csv(
                    file_path,
                    index=False
                )
                log(
                    f"✅ Saved signals for "
                    f"{yr} | rows={len(signals)}"
                )
                if yr == start_year:
                    current_year.append(signals)

            except Exception as e:
                log(
                    f"❌ Error processing "
                    f"year {yr}: {str(e)}"
                )
                continue
        # ==========================================================
        # DISPLAY
        # ==========================================================
        if not current_year:
            log(
                "⚠️ No current year signals found"
            )
            return pd.DataFrame()
        display_df = display_logic(
            current_year[0]
        )

        log(
            f"🏁 Scanner completed: "
            f"{scanner_name}"
        )

        return display_df
    except Exception as e:

        log(
            f"🚨 Fatal scanner error: "
            f"{str(e)}"
        )

        return pd.DataFrame()
# --------------------------------------------------------------------------