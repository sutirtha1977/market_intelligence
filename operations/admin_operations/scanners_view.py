# operations/admin_operations/scanners_view.py

import streamlit as st
from streamlit_option_menu import option_menu
from datetime import datetime
import pandas as pd

from config.logger import clear_log
from core.ui_helpers import action_button, run_operation
from core.widgets import get_vertical_tab_styles
from config.db_config import ASSET_CHOICE_MAP

from services.scanners.scanners_final.weekly_signal import update_scanner_weekly
from services.scanners.scanners_final.momentum_signals import update_scanner_momentum

# --------------------------------------------------------------------------
st.session_state.setdefault("scanners_message", None)
st.session_state.setdefault("selected_operation", "Select Scanner Operation")
st.session_state.setdefault("scanner_asset_select", list(ASSET_CHOICE_MAP.keys())[0])
# --------------------------------------------------------------------------
def operation_scanner(scanner_type: str, update_fn):

    current_year = datetime.now().year

    asset_label = st.selectbox(
        "Select Asset Type",
        options=list(ASSET_CHOICE_MAP.keys())[:2],
        key="scanner_asset_select"
    )

    asset_type = ASSET_CHOICE_MAP[asset_label]

    def task():
        clear_log()

        count = update_fn(
            asset_type=asset_type,
            scanner_type=scanner_type
        )

        st.session_state.scanners_message = (
            f"{count} signals processed for {asset_label} "
            f"({scanner_type.upper()} | {current_year})"
        )

        # Reset UI state
        st.session_state.symbol_map = {}
        st.session_state.chart_data = pd.DataFrame()
        st.session_state.selected_symbol = None

    action_button(
        f"Update {scanner_type.capitalize()} Scanner",
        run_operation(
            f"Running {scanner_type} scanner for ({current_year})...",
            task
        )
    )

# --------------------------------------------------------------------------
def handle_scanners_operations():

    operations = [
        "Select Scanner Operation",
        "Weekly",
        "Momentum"
    ]

    operations_map = {
        "Weekly": lambda: operation_scanner("weekly", update_scanner_weekly),
        "Momentum": lambda: operation_scanner("momentum", update_scanner_momentum)
    }

    choice = option_menu(
        menu_title=None,
        options=operations,
        icons=["tools", "calendar", "activity"],
        orientation="vertical",
        default_index=operations.index(
            st.session_state.selected_operation
        ) if st.session_state.selected_operation in operations else 0,
        key="scanner_menu",
        styles=get_vertical_tab_styles()
    )

    st.session_state.selected_operation = choice

    if choice in operations_map:
        operations_map[choice]()

    if st.session_state.scanners_message:
        st.info(st.session_state.scanners_message)
        st.session_state.scanners_message = None

# --------------------------------------------------------------------------
