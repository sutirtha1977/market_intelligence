# operations/admin_operations/nse_view.py

import streamlit as st
from streamlit_option_menu import option_menu
from config.logger import log, clear_log
from core.ui_helpers import action_button,run_operation, show_message
from core.widgets import get_vertical_tab_styles

from services.index.nse_data_service import upsert_nifty_index_constituents
from services.index.nse_data_service import upsert_nse_index_history
from services.index.nse_data_service import upsert_nse_index_incremental
from services.index.nse_data_service import update_weekly_monthly_for_all_symbols
from services.equity.indicator.indicator_engine import refresh_indicators
from services.index.nse_data_service import update_nse_index_srt
from services.index.vix_service import update_vix_daily_data
from services.index.vix_service import compute_vix_features_talib
from services.equity.indicator.rs_engine import run_rs_engine

# --------------------------------------------------------------------------
st.session_state.setdefault("nse_message", None)
# --------------------------------------------------------------------------
def operation_constituents():
    def task():
        clear_log()
        try:
            log("Updating index constituents")
            upsert_nifty_index_constituents()
            st.session_state.nse_message = "Index constituents synced successfully."
        except Exception as e:
            st.session_state.nse_message = f"ERROR {e}"
    action_button(
        "Sync Constituents",
        run_operation("Updating constituents...", task)
    )
    
# --------------------------------------------------------------------------
def operation_history():
    def task():
        clear_log()
        try:
            log("Loading historical data")
            upsert_nse_index_history()
            st.session_state.nse_message = "Historical data loaded successfully."
        except Exception as e:
            st.session_state.nse_message = f"ERROR {e}"
    action_button(
        "Load Historical Data",
        run_operation("Loading historical data...", task)
    )
    
# --------------------------------------------------------------------------
def operation_incremental():
    def task():
        clear_log()
        try:
            log("Updating incremental data")
            upsert_nse_index_incremental()
            st.session_state.nse_message = "Incremental data updated successfully."
        except Exception as e:
            st.session_state.nse_message = f"ERROR {e}"
    action_button(
        "Update Incremental Data",
        run_operation("Updating incremental data...", task)
    )
    
# --------------------------------------------------------------------------
def operation_weekly_monthly():
    def task():
        clear_log()
        try:
            log("Updating weekly/monthly data")
            update_weekly_monthly_for_all_symbols(asset_type="nse_india_index")
            st.session_state.nse_message = "Weekly & Monthly data updated successfully."
        except Exception as e:
            st.session_state.nse_message = f"ERROR {e}"
    action_button(
        "Update Weekly/Monthly",
        run_operation("Updating weekly/monthly data...", task)
    )
    
# --------------------------------------------------------------------------
def operation_indicators():
    def task():
        clear_log()
        try:
            log("Refreshing indicators")
            refresh_indicators(asset_types=["nse_india_index"])
            st.session_state.nse_message = "Index indicators updated successfully."
        except Exception as e:
            st.session_state.nse_message = f"ERROR {e}"
    action_button(
        "Refresh Indicators",
        run_operation("Refreshing index indicators...", task)
    )
    
# --------------------------------------------------------------------------
def operation_srt(): 
    def task():
        clear_log()
        try:
            log("Updating Daily SRT for index")
            update_nse_index_srt()
            st.session_state.nse_message = "SRT updated successfully."
        except Exception as e:
            st.session_state.nse_message = f"ERROR {e}"
    action_button(
        "Update SRT",
        run_operation("Updating Daily SRT...", task)
    )

# --------------------------------------------------------------------------
def operation_rs():
    def task():
        clear_log()
        try:
            log("Updating Daily RS for index")
            run_rs_engine("nse_india_index")
            st.session_state.nse_message = "RS updated successfully."
        except Exception as e:
            st.session_state.nse_message = f"ERROR {e}"
    action_button(
        "Update Daily RS",
        run_operation("Updating Daily RS...", task)
    )
# --------------------------------------------------------------------------
def operation_update_vix():
    def task():
        clear_log()
        try:
            log("Starting VIX daily update")
            update_vix_daily_data()
            st.session_state.nse_message = "VIX price data updated successfully."
        except Exception as e:
            log(f"ERROR in VIX update: {e}")
            st.session_state.nse_message = f"ERROR {e}"

    action_button(
        "Update VIX Data",
        run_operation("Updating VIX data...", task)
    )
# --------------------------------------------------------------------------
def operation_compute_vix_features():
    def task():
        clear_log()
        try:
            log("Starting VIX feature computation (TA-Lib)")
            compute_vix_features_talib()
            st.session_state.nse_message = "VIX features computed successfully."
        except Exception as e:
            log(f"ERROR in VIX feature computation: {e}")
            st.session_state.nse_message = f"ERROR {e}"

    action_button(
        "Compute VIX Features",
        run_operation("Computing VIX features...", task)
    ) 
# --------------------------------------------------------------------------
def handle_nse_operations():
    # show_message("nse_message")
    operations = [
        "Select NSE Operation",
        "Sync Constituents",
        "Load Historical Data",
        "Update Incremental Data",
        "Weekly & Monthly Data",
        "Refresh Indicators",
        "Update Daily SRT",
        "Update Daily RS",
        "Update VIX Price Data",
        "Compute VIX Features"
    ]

    operations_map = {
        "Sync Constituents": operation_constituents,
        "Load Historical Data": operation_history,
        "Update Incremental Data": operation_incremental,
        "Weekly & Monthly Data": operation_weekly_monthly,
        "Refresh Indicators": operation_indicators,
        "Update Daily SRT": operation_srt,
        "Update Daily RS": operation_rs,
        "Update VIX Price Data": operation_update_vix,
        "Compute VIX Features": operation_compute_vix_features
    }

    choice = option_menu(
        menu_title=None,
        options=operations,
        icons=["tools", 
               "gear", 
               "book", 
               "arrow-repeat", 
               "calendar", 
               "bar-chart-line", 
               "lightning", 
               "activity",
               "gear", 
               "cpu"
            ],
        menu_icon="",
        default_index=0,
        orientation="vertical",
        styles=get_vertical_tab_styles()
    )
    show_message("nse_message")
    if choice in operations_map:
        operations_map[choice]()
# --------------------------------------------------------------------------