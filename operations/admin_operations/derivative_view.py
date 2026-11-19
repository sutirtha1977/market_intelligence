# operations/admin_operations/derivative_view.py

import streamlit as st
from streamlit_option_menu import option_menu
from datetime import date
from config.logger import log, clear_log
from core.ui_helpers import action_button, run_operation, show_message
from core.widgets import get_vertical_tab_styles
from services.derivatives.bhavcopy_service import download_and_load_bhavcopies
from services.derivatives.indicator_service import refresh_futures_indicators
from services.derivatives.greeks_service import update_all_options_greeks
from services.derivatives.pcr_service import calculate_and_upsert_pcr
from services.derivatives.iv_service import update_all_iv_stats
from services.derivatives.expiry_service import update_all_expiry_metrics

# --------------------------------------------------------------------------
st.session_state.setdefault("derivative_message", None)
# --------------------------------------------------------------------------
def operation_incremental():
    def task():
        clear_log()
        try:
            log("Starting incremental bhavcopy")
            download_and_load_bhavcopies(folder_type="incremental")
            st.session_state.derivative_message = "Incremental BhavCopy processed successfully."
        except Exception as e:
            st.session_state.derivative_message = f"ERROR {e}"
    action_button(
        "Run Incremental",
        run_operation("Processing incremental bhavcopy...", task)
    )

# --------------------------------------------------------------------------
def operation_historical():
    period = st.selectbox(
        "Bhavcopy Period :",
        ["After 8th June 2024", "Before 8th June 2024"]
    )
    if period == "Before 8th June 2024":
        default_start = date(2020, 1, 1)
        default_end = date(2024, 6, 7)
        folder_type = "old"
    else: 
        default_start = date(2024, 6, 8)
        default_end = date.today()
        folder_type = "historical"
    c1, c2 = st.columns(2)
    with c1:
        start_date = st.date_input(
            "Start Date :",
            value=default_start,
            min_value=default_start,
            max_value=default_end
        )
    with c2:
        end_date = st.date_input(
            "End Date :",
            value=default_end,
            min_value=default_start,
            max_value=default_end
        )
    def task():
        clear_log()
        try:
            log(f"Historical bhavcopy: {start_date} → {end_date} | folder_type={folder_type}")
            download_and_load_bhavcopies(
                start_date=start_date,
                end_date=end_date,
                folder_type=folder_type
            )
            st.session_state.derivative_message = f"Historical BhavCopy processed successfully ({start_date} → {end_date})"
        except Exception as e:
            log(f"ERROR in historical bhavcopy: {e}")
            st.error(f"ERROR: {e}")
    action_button(
        "Run Historical",
        run_operation("Processing historical bhavcopies...", task)
    )

# --------------------------------------------------------------------------
def operation_indicators():
    def task():
        clear_log()
        try:
            log("Refreshing F&O indicators")
            refresh_futures_indicators(timeframe="1d")
            st.session_state.derivative_message = "Derivatives indicators updated successfully."
        except Exception as e:
            st.session_state.derivative_message = f"ERROR {e}"
    action_button(
        "Update Indicators",
        run_operation("Updating F&O indicators...", task)
    )

# --------------------------------------------------------------------------
def operation_greeks():
    def task():
        clear_log()
        try:
            log(f"Updating Greeks")
            update_all_options_greeks()
            st.session_state.derivative_message = f"Options Greeks updated successfully "
        except Exception as e:
            st.session_state.derivative_message = f"ERROR {e}"
    action_button(
        "Update Greeks",
        run_operation("Updating Greeks...", task)
    )
# --------------------------------------------------------------------------
def operation_pcr():
    def task():
        clear_log()
        try:
            log("Calculating PCR for all data (stocks + indices)")
            calculate_and_upsert_pcr()  # no date → full dataset
            st.session_state.derivative_message = "PCR calculated and updated successfully."
        except Exception as e:
            log(f"ERROR in PCR calculation: {e}")
            st.session_state.derivative_message = f"ERROR {e}"
    action_button(
        "Calculate PCR",
        run_operation("Calculating PCR (full dataset)...", task)
    )
# --------------------------------------------------------------------------
def operation_iv():
    def task():
        clear_log()
        try:
            log("Updating IV stats (incremental: stocks + indices)")
            update_all_iv_stats()
            st.session_state.derivative_message = "IV calculated and updated successfully."
        except Exception as e:
            log(f"ERROR in IV calculation: {e}")
            st.session_state.derivative_message = f"ERROR {e}"
    action_button(
        "Calculate IV",
        run_operation("Calculating IV (full dataset)...", task)
    )
# --------------------------------------------------------------------------
def operation_expiry_metrics():
    def task():
        clear_log()
        try:
            log("Calculating Expiry Metrics (stocks + indices)")
            update_all_expiry_metrics()
            st.session_state.derivative_message = "Expiry Metrics calculated and updated successfully."
        except Exception as e:
            log(f"ERROR in Expiry Metrics calculation: {e}")
            st.session_state.derivative_message = f"ERROR {e}"

    action_button(
        "Calculate Expiry Metrics",
        run_operation("Calculating Expiry Metrics...", task)
    )
# --------------------------------------------------------------------------
# def handle_derivative_operations():
#     msg = st.session_state.get("derivative_message")
#     operations = [
#         "Select Derivative Operation",
#         "Historical Bhavcopy",
#         "Incremental Bhavcopy",
#         "Refresh Indicators",
#         "Update PCR",
#         "Update Greeks",
#         "Update IV",
#         "Calculate Expiry Metrics"
#     ]
#     operations_map = {
#         "Historical Bhavcopy": operation_historical,
#         "Incremental Bhavcopy": operation_incremental,
#         "Refresh Indicators": operation_indicators,
#         "Update PCR": operation_pcr,
#         "Update Greeks": operation_greeks,
#         "Update IV" : operation_iv,
#         "Calculate Expiry Metrics": operation_expiry_metrics
#     }
#     choice = option_menu(
#         menu_title=None,
#         options=operations,
#         icons=["tools", 
#                "calendar-check", 
#                "clock-history", 
#                "bar-chart-line-fill", 
#                "activity", 
#                "calculator", 
#                "speedometer", 
#                "diagram-3-fill"
#         ],
#         menu_icon="",
#         default_index=0,
#         orientation="vertical",
#         styles=get_vertical_tab_styles()
#     )
#     st.markdown('</div>', unsafe_allow_html=True)
#     if msg:
#         if msg.startswith("ERROR"):
#             st.error(msg)
#         else:
#             st.info(msg)
#         st.session_state.derivative_message = None
#     if choice in operations_map:
#         operations_map[choice]()
def handle_derivative_operations():
    # show_message("derivative_message")
    
    operations = [
        "Select Derivative Operation",
        "Historical Bhavcopy",
        "Incremental Bhavcopy",
        "Refresh Indicators",
        "Update PCR",
        "Update Greeks",
        "Update IV",
        "Calculate Expiry Metrics"
    ]

    operations_map = {
        "Historical Bhavcopy": operation_historical,
        "Incremental Bhavcopy": operation_incremental,
        "Refresh Indicators": operation_indicators,
        "Update PCR": operation_pcr,
        "Update Greeks": operation_greeks,
        "Update IV": operation_iv,
        "Calculate Expiry Metrics": operation_expiry_metrics
    }

    choice = option_menu(
        menu_title=None,
        options=operations,
        icons=[
            "tools",
            "calendar-check",
            "clock-history",
            "bar-chart-line-fill",
            "activity",
            "calculator",
            "speedometer",
            "diagram-3-fill"
        ],
        menu_icon="",
        default_index=0,
        orientation="vertical",
        styles=get_vertical_tab_styles()
    )
    show_message("derivative_message")
    if choice in operations_map:
        operations_map[choice]()
# --------------------------------------------------------------------------