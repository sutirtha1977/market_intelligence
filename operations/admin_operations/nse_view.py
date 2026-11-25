# operations/admin_operations/nse_view.py

import streamlit as st
from streamlit_option_menu import option_menu

from config.logger import log, clear_log
from core.ui_helpers import action_button, show_message
from core.widgets import get_vertical_tab_styles

st.session_state.setdefault("nse_message", None)


def run_nse_task(button_label, progress_message, success_message, operation, *args, **kwargs):
    def task():
        try:
            clear_log()
            log(progress_message)
            operation(*args, **kwargs)
            st.session_state.nse_message = success_message
        except Exception as exc:
            log(f"ERROR: {exc}", level="error")
            st.session_state.nse_message = f"ERROR: {exc}"

    action_button(button_label, task)


def operation_constituents():
    from services.index.nse_data_service import upsert_nifty_index_constituents

    run_nse_task(
        "Sync Constituents",
        "Updating index constituents",
        "Index constituents synced successfully.",
        upsert_nifty_index_constituents,
    )


def operation_history():
    from services.index.nse_data_service import upsert_nse_index_history

    run_nse_task(
        "Load Historical Data",
        "Loading historical data",
        "Historical data loaded successfully.",
        upsert_nse_index_history,
    )


def operation_incremental():
    from services.index.nse_data_service import upsert_nse_index_incremental

    run_nse_task(
        "Update Incremental Data",
        "Updating incremental data",
        "Incremental data updated successfully.",
        upsert_nse_index_incremental,
    )


def operation_weekly_monthly():
    from services.index.nse_data_service import update_weekly_monthly_for_all_symbols

    run_nse_task(
        "Update Weekly/Monthly",
        "Updating weekly/monthly data",
        "Weekly & Monthly data updated successfully.",
        update_weekly_monthly_for_all_symbols,
        asset_type="nse_india_index",
    )


def operation_indicators():
    from services.equity.indicator.indicator_engine import refresh_indicators

    run_nse_task(
        "Refresh Indicators",
        "Refreshing indicators",
        "Index indicators updated successfully.",
        refresh_indicators,
        asset_types=["nse_india_index"],
    )


def operation_srt():
    from services.index.nse_data_service import update_nse_index_srt

    run_nse_task(
        "Update SRT",
        "Updating Daily SRT for index",
        "SRT updated successfully.",
        update_nse_index_srt,
    )


def operation_update_vix():
    from services.index.vix_service import update_vix_daily_data

    run_nse_task(
        "Update VIX Data",
        "Starting VIX daily update",
        "VIX price data updated successfully.",
        update_vix_daily_data,
    )


def operation_compute_vix_features():
    from services.index.vix_service import compute_vix_features_talib

    run_nse_task(
        "Compute VIX Features",
        "Starting VIX feature computation (TA-Lib)",
        "VIX features computed successfully.",
        compute_vix_features_talib,
    )


def handle_nse_operations():
    message_placeholder = st.empty()
    run_type = st.segmented_control(
        "Run type",
        options=["Daily run", "One-time run"],
        default="Daily run",
        key="nse_run_type",
    )

    selected_group = "Daily run" if run_type == "Daily run" else "One-time run"
    operations_by_group = {
        "One-time run": [
            "Select Operation",
            "Sync Constituents",
            "Load Historical Data",
        ],
        "Daily run": [
            "Select Operation",
            "Update Incremental Data",
            "Weekly & Monthly Data",
            "Refresh Indicators",
            "Update Daily SRT",
            "Update VIX Price Data",
            "Compute VIX Features",
        ],
    }
    icons_by_group = {
        "One-time run": ["tools", "gear", "book"],
        "Daily run": [
            "tools",
            "arrow-repeat",
            "calendar",
            "bar-chart-line",
            "lightning",
            "gear",
            "cpu",
        ],
    }

    operations_map = {
        "Sync Constituents": operation_constituents,
        "Load Historical Data": operation_history,
        "Update Incremental Data": operation_incremental,
        "Weekly & Monthly Data": operation_weekly_monthly,
        "Refresh Indicators": operation_indicators,
        "Update Daily SRT": operation_srt,
        "Update VIX Price Data": operation_update_vix,
        "Compute VIX Features": operation_compute_vix_features,
    }

    choice = option_menu(
        menu_title=None,
        options=operations_by_group[selected_group],
        icons=icons_by_group[selected_group],
        menu_icon="",
        default_index=0,
        orientation="vertical",
        styles=get_vertical_tab_styles(),
        key=(
            "nse_daily_operation_menu"
            if selected_group == "Daily run"
            else "nse_one_time_operation_menu"
        ),
    )

    if choice in operations_map:
        operations_map[choice]()

    with message_placeholder.container():
        show_message("nse_message")