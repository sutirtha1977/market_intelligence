import os
import pandas as pd
from datetime import date
from typing import Tuple
from config.paths import SCANNER_DIR
from config.logger import log
from services.equity.cleanup_service import delete_files_in_folder
from services.scanners.backtest_weekly.data_engine_weekly import data_logic
from services.scanners.backtest_weekly.logic_engine_weekly import scanner_logic
from services.scanners.backtest_weekly.backtest_engine_weekly import backtest_logic
from services.scanners.backtest_weekly.display_engine_weekly import display_logic

# --------------------------------------------------------------------------
def scanner_backtest_weekly(
    asset_type: str = "india_equity_yahoo",
    start_year: int = date.today().year,
    lookback_years: int = 5,
    target_pct: float = 5.0,
    scanner_name: str = "weekly"
) -> Tuple[pd.DataFrame, pd.DataFrame]:

    try:
        base_folder = os.path.join(SCANNER_DIR, scanner_name, asset_type)
        os.makedirs(base_folder, exist_ok=True)

        delete_files_in_folder(base_folder)

        current_year = []

        for yr in range(start_year, start_year - lookback_years, -1):

            try:
                log(f"🔍 Running scanner: {scanner_name} | Year: {yr}")

                df = data_logic(
                    asset_type,
                    f"{yr}-01-01",
                    f"{yr}-12-31"
                )

                if df is None or df.empty:
                    log(f"⚠️ No data for {yr}")
                    continue

                signals = scanner_logic(df, asset_type)

                if signals is None or signals.empty:
                    log(f"⚠️ No signals for {yr}")
                    continue

                # file_path = os.path.join(base_folder, f"WEEKLY_{yr}.csv")
                file_path = os.path.join(base_folder, f"{scanner_name.upper()}_{yr}.csv")
                signals.to_csv(file_path, index=False)

                log(f"✅ Saved signals for {yr} | rows={len(signals)}")

                if yr == start_year:
                    current_year.append(signals)

            except Exception as e:
                log(f"❌ Error processing year {yr}: {str(e)}")
                continue

        # ==========================================================
        # BACKTEST
        # ==========================================================
        backtest_df = backtest_logic(
            asset_type,
            base_folder,
            target_pct
        )

        display_df = display_logic(current_year[0])
        
        log(f"🏁 Scanner completed: {scanner_name}")
        
        return backtest_df, display_df

    except Exception as e:
        log(f"🚨 Fatal scanner error: {str(e)}")
        return pd.DataFrame(), pd.DataFrame()
    
# --------------------------------------------------------------------------