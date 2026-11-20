# operations/admin_operations/yahoo_view.py

import streamlit as st
from streamlit_option_menu import option_menu
from datetime import datetime
from config.logger import log, clear_log
from config.db_config import ASSET_CHOICE_MAP
from core.ui_helpers import action_button, show_message
from core.widgets import get_horizontal_internal_tab_styles
from services.equity.yahoo.yahoo_service import insert_yahoo_price_data
from services.equity.indicator.indicator_engine import refresh_indicators
# --------------------------------------------------------------------------
st.session_state.setdefault("yahoo_message", None)
# --------------------------------------------------------------------------
def get_asset_choice(key: str) -> tuple[str, str]:
    asset_label = st.selectbox(
        "Asset type",
        list(ASSET_CHOICE_MAP.keys()),
        key=key
    )
    return asset_label, ASSET_CHOICE_MAP[asset_label]
# --------------------------------------------------------------------------
def operation_price_data(progress_placeholder):
    asset_label, asset_type = get_asset_choice("yahoo_price_asset")
    symbols = st.text_input(
        "Symbols",
        value="ALL",
        key="yahoo_symbols",
        help="Enter symbols to update: ALL or comma-separated (e.g., RELIANCE,TCS,INFY)."
    ).strip()
    start_date = st.date_input(
        "Start date",
        value=datetime(1999, 1, 1),
        min_value=datetime(1980, 1, 1),
        max_value=datetime.today(),
        key="yahoo_start_date"
    )
    def task():
        clear_log()
        try:
            log(f"Yahoo update: {asset_type} {symbols}")

            progress_placeholder.progress(0.0, text="Preparing Yahoo update...")

            def update_progress(timeframe: str, completed: int, total: int) -> None:
                progress = completed / total if total else 1.0
                progress_placeholder.progress(
                    progress,
                    text=f"Timeframe {timeframe}: {completed}/{total} symbols"
                )

            failed = insert_yahoo_price_data(
                asset_type=asset_type,
                symbols=symbols,
                start_date=start_date.strftime("%Y-%m-%d"),
                progress_callback=update_progress,
            )
            if failed:
                st.session_state.yahoo_message = f"FAILED: {', '.join(failed)}"
            else:
                st.session_state.yahoo_message = f"{asset_label} Price Data update successful."
        except Exception as e:
            st.session_state.yahoo_message = f"Error: {e}"
    action_button(
        "Update Price Data",
        task
    ) 
# --------------------------------------------------------------------------
def operation_indicators(progress_placeholder):
    asset_label, asset_type = get_asset_choice("yahoo_indicator_asset")
    def task():
        try:
            log(f"Refreshing indicators for {asset_type}")

            progress_placeholder.progress(0.0, text="Preparing indicator refresh...")

            def update_progress(timeframe: str, completed: int, total: int) -> None:
                progress = completed / total if total else 1.0
                progress_placeholder.progress(
                    progress,
                    text=f"Timeframe {timeframe}: {completed}/{total} symbols"
                )

            refresh_indicators(
                asset_types=[asset_type],
                progress_callback=update_progress,
            )
            st.session_state.yahoo_message = f"{asset_label} Indicators update successful."
        except Exception as e:
            st.session_state.yahoo_message = f"ERROR: {e}"
    action_button(
        "Refresh Indicators",
        task
    )
# --------------------------------------------------------------------------
def operation_vcp(): 
    from services.equity.indicator.vcp_engine import run_vcp_engine
    asset_label, asset_type = get_asset_choice("yahoo_vcp_asset")
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
        task
    )
# --------------------------------------------------------------------------
def handle_yahoo_operations():

    operations = ["PRICE DATA", "INDICATORS", "VCP"]

    choice = option_menu(
        menu_title=None,
        options=operations,
        icons=["cloud-download", "bar-chart-line", "graph-up-arrow"],
        menu_icon="",
        default_index=0,
        orientation="horizontal",
        styles=get_horizontal_internal_tab_styles()
    )

    with st.container():
        message_placeholder = st.empty()
        progress_placeholder = st.empty()

    operations_map = {
        "PRICE DATA": lambda: operation_price_data(progress_placeholder),
        "INDICATORS": lambda: operation_indicators(progress_placeholder),
        "VCP": operation_vcp
    }

    if choice in operations_map:
        operations_map[choice]()

    with message_placeholder.container():
        show_message("yahoo_message")
        
# --------------------------------------------------------------------------
