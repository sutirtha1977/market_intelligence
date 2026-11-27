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
def section_header(title: str, description: str) -> None:
    st.markdown(f"#### {title}")
    st.caption(description)
# --------------------------------------------------------------------------
def operation_price_data(progress_placeholder):
    section_header(
        "Price data",
        "Download historical prices from Yahoo Finance for the selected asset type."
    )

    asset_col, symbols_col, date_col = st.columns([1.2, 2, 1.2])
    with asset_col:
        asset_label, asset_type = get_asset_choice("yahoo_price_asset")
    with symbols_col:
        symbols = st.text_input(
            "Symbols",
            value="ALL",
            key="yahoo_symbols",
            help="Enter symbols to update: ALL or comma-separated (e.g., RELIANCE,TCS,INFY)."
        ).strip()
    with date_col:
        start_date = st.date_input(
            "Start date",
            value=datetime(1999, 1, 1),
            min_value=datetime(1980, 1, 1),
            max_value=datetime.today(),
            key="yahoo_start_date"
        )

    st.divider()

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
        task,
        transparent_overlay=True
    )
# --------------------------------------------------------------------------
def operation_indicators(progress_placeholder):
    section_header(
        "Indicators",
        "Recalculate technical indicators for every symbol of the selected asset type."
    )

    asset_col, _ = st.columns([1.2, 3.2])
    with asset_col:
        asset_label, asset_type = get_asset_choice("yahoo_indicator_asset")

    st.divider()

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
        task,
        transparent_overlay=True
    )
# --------------------------------------------------------------------------
def operation_additional(progress_placeholder):
    section_header(
        "Additional operations",
        "Supplementary calculations that run on top of the price data."
    )

    select_col, _ = st.columns([2, 2.4])
    with select_col:
        selection = st.selectbox(
            "Additional operation",
            ["RS for India Equity"],
            key="yahoo_additional_operation"
        )

    st.divider()

    def task():
        try:
            if selection == "RS for India Equity":
                from services.equity.indicator.rs_engine import run_rs_engine

                asset_type = ASSET_CHOICE_MAP["INDIA Equity"]
                log(f"Starting RS computation for {asset_type}")

                progress_placeholder.progress(
                    0.0,
                    text="Preparing RS update..."
                )

                def update_progress(
                    timeframe: str,
                    phase: str,
                    completed: int,
                    total: int
                ) -> None:
                    progress = completed / total if total else 0.0
                    progress_placeholder.progress(
                        progress,
                        text=f"Timeframe {timeframe} - {phase}: {completed}/{total}"
                    )

                run_rs_engine(
                    asset_type=asset_type,
                    progress_callback=update_progress,
                )
                st.session_state.yahoo_message = "India Equity Relative Strength update successful."
        except Exception as e:
            st.session_state.yahoo_message = f"ERROR: {e}"

    action_button(
        "Update Relative Strength",
        task,
        transparent_overlay=True
    )
# --------------------------------------------------------------------------
def handle_yahoo_operations():

    # st.subheader("Yahoo Finance data")
    # st.caption("Update prices, indicators and relative strength for equity assets.")

    operations = ["Price data", "Indicators", "Additional"]

    choice = option_menu(
        menu_title=None,
        options=operations,
        icons=["cloud-download", "bar-chart-line", "graph-up-arrow"],
        menu_icon="",
        default_index=0,
        orientation="horizontal",
        styles=get_horizontal_internal_tab_styles()
    )

    # Same order as the original: result message, then progress bar, then the form.
    message_placeholder = st.empty()
    progress_placeholder = st.empty()

    with st.container(border=True):
        form_container = st.container()

    operations_map = {
        "Price data": lambda: operation_price_data(progress_placeholder),
        "Indicators": lambda: operation_indicators(progress_placeholder),
        "Additional": lambda: operation_additional(progress_placeholder)
    }

    if choice in operations_map:
        with form_container:
            operations_map[choice]()

    with message_placeholder.container():
        show_message("yahoo_message")
# --------------------------------------------------------------------------