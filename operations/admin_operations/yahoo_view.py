# operations/admin_operations/yahoo_view.py

import streamlit as st
from streamlit_option_menu import option_menu
from datetime import datetime
from config.logger import log, clear_log
from config.db_config import ASSET_CHOICE_MAP
from core.ui_helpers import action_button, run_operation, show_message
from core.widgets import get_horizontal_internal_tab_styles, get_vertical_tab_styles
from services.equity.yahoo.yahoo_service import insert_yahoo_price_data
from services.equity.indicator.indicator_engine import refresh_indicators
# --------------------------------------------------------------------------
st.session_state.setdefault("yahoo_message", None)
# --------------------------------------------------------------------------
def operation_price_data():
    asset_label = st.radio(
        "Select Asset Type :",
        list(ASSET_CHOICE_MAP.keys()),
        key="yahoo_price_asset",
        horizontal= True
    )
    asset_type = ASSET_CHOICE_MAP[asset_label]
    symbols = st.text_input(
        "Symbols :",
        value="ALL",
        key="yahoo_symbols",
        help="Enter symbols to update: ALL or comma-separated (e.g., RELIANCE,TCS,INFY)."
    ).strip()
    start_date = st.date_input(
        "Start Date :",
        value=datetime(1999, 1, 1),
        min_value=datetime(1980, 1, 1),
        max_value=datetime.today(),
        key="yahoo_start_date"
    )
    def task():
        clear_log()
        try:
            log(f"Yahoo update: {asset_type} {symbols}")
            failed = insert_yahoo_price_data(
                asset_type=asset_type,
                symbols=symbols,
                start_date=start_date.strftime("%Y-%m-%d")
            )
            if failed:
                st.session_state.yahoo_message = f"FAILED: {', '.join(failed)}"
            else:
                st.session_state.yahoo_message = f"{asset_label} Price Data update successful."
        except Exception as e:
            st.session_state.yahoo_message = f"Error: {e}"
    action_button(
        "Update Price Data",
        run_operation("Downloading Yahoo data...", task)
    ) 
# --------------------------------------------------------------------------
def operation_indicators():
    asset_label = st.radio(
        "Select Asset Type :",
        list(ASSET_CHOICE_MAP.keys()),
        key="yahoo_indicator_asset",
        horizontal=True
    )
    asset_type = ASSET_CHOICE_MAP[asset_label]
    def task():
        clear_log()
        try:
            log(f"Refreshing indicators for {asset_type}")
            refresh_indicators(asset_types=[asset_type])
            st.session_state.yahoo_message = f"{asset_label} Indicators update successful."
        except Exception as e:
            st.session_state.yahoo_message = f"Error: {e}"
    action_button(
        "Refresh Indicators",
        run_operation(f"Refreshing indicators for {asset_label}...", task)
    )
# --------------------------------------------------------------------------
def operation_vcp(): 
    from services.equity.indicator.vcp_engine import run_vcp_engine
    asset_label = st.radio(
        "Select Asset Type :",
        list(ASSET_CHOICE_MAP.keys()),
        key="yahoo_indicator_asset",
        horizontal=True
    )
    asset_type = ASSET_CHOICE_MAP[asset_label]
    def task():
        # clear_log()
        try:
            log(f"Starting VCP computation for {asset_type}")
            run_vcp_engine(asset_type=asset_type)
            st.session_state.yahoo_message = f"{asset_label} VCP Data update successful."
        except Exception as e:
            st.session_state.yahoo_message = f"Error: {e}"

    action_button(
        "Compute VCP Data",
        run_operation("Computing VCP Data...", task)
    )
# --------------------------------------------------------------------------
def handle_yahoo_operations():

    operations = ["PRICE DATA", "INDICATORS", "VCP"]

    operations_map = {
        "PRICE DATA": operation_price_data,
        "INDICATORS": operation_indicators,
        "VCP": operation_vcp
    }

    choice = option_menu(
        menu_title=None,
        options=operations,
        icons=["cloud-download", "bar-chart-line", "graph-up-arrow"],
        menu_icon="",
        default_index=0,
        orientation="horizontal",
        styles=get_horizontal_internal_tab_styles()
    )

    show_message("yahoo_message")

    if choice in operations_map:
        operations_map[choice]()
        
# --------------------------------------------------------------------------
