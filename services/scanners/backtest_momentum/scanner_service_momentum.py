import os
import pandas as pd
from datetime import date
from typing import Tuple

from config.paths import SCANNER_DIR
from config.logger import log
from services.equity.cleanup_service import delete_files_in_folder
from services.scanners.backtest_momentum.data_engine_momentum import data_logic
from services.scanners.backtest_momentum.backtest_engine_momentum import backtest_logic
from services.scanners.backtest_momentum.display_engine_momentum import display_logic   # ✅ ADD THIS

# --------------------------------------------------------------------------
def scanner_backtest_momentum(
    asset_type: str = "india_equity_yahoo",
    start_year: int = date.today().year,
    lookback_years: int = 5,
    target_pct: float = 5.0,
    scanner_name: str = "momentum"
) -> Tuple[pd.DataFrame, pd.DataFrame]:

    try:
        base_folder = os.path.join(SCANNER_DIR, scanner_name, asset_type)
        os.makedirs(base_folder, exist_ok=True)

        delete_files_in_folder(base_folder)

        current_year_df = None

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

                file_path = os.path.join(
                    base_folder,
                    f"{scanner_name.upper()}_{yr}.csv"
                )

                df.to_csv(file_path, index=False)

                log(f"✅ Saved signals for {yr} | rows={len(df)}")

                # store ONLY latest year
                if yr == start_year:
                    current_year_df = df.copy()

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

        # ==========================================================
        # FINAL DISPLAY DF (MATCH WEEKLY STRUCTURE)
        # ==========================================================
        if current_year_df is None or current_year_df.empty:
            display_df = pd.DataFrame()
        else:
            display_df = display_logic(current_year_df)   # ✅ KEY CHANGE

        log(f"🏁 Scanner completed: {scanner_name}")

        return backtest_df, display_df

    except Exception as e:
        log(f"🚨 Fatal scanner error: {str(e)}")
        return pd.DataFrame(), pd.DataFrame()

# --------------------------------------------------------------------------