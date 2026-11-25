# operations/admin_operations/database_view.py

import streamlit as st
from config.logger import log, clear_log
from core.ui_helpers import action_button, show_message
from database.create_equity_database import create_equity_database
# from database.create_fno_database import create_fno_database
from services.equity.symbol_service import refresh_symbols
from services.equity.utility_service import upsert_nse_holidays

# --------------------------------------------------------------------------
st.session_state.setdefault("db_message", None)
st.session_state.setdefault("db_dates_df", None)
# --------------------------------------------------------------------------
# def operation_create_database():
#     db_type = st.radio(
#         label="Select Database Type :",
#         options=["Equity", "Derivative"],
#         key="db_create_type",
#         horizontal=True,
#         label_visibility="visible"
#     )
#     drop_existing = st.checkbox(
#         "Drop existing tables (❌ DANGEROUS)",
#         key="db_drop_existing"
#     )
#     def task():
#         clear_log()
#         try:
#             log(f"Creating {db_type}, drop={drop_existing}")
#             if db_type.upper() == "EQUITY":
#                 create_equity_database(drop_existing)
#             else:
#                 create_fno_database(drop_existing)
#             st.session_state.db_message = f"{db_type} created successfully!"
#         except Exception as e:
#             st.session_state.db_message = f"ERROR {e}"
#     action_button(
#         "Create Database",
#         run_operation("Creating database...", task)
#     )
def operation_create_database():
    drop_existing = st.checkbox(
        "Drop existing tables (❌ DANGEROUS)",
        key="db_drop_existing"
    )
    def task():
        try:
            clear_log()
            log(f"Creating Equity database, drop={drop_existing}")

            create_equity_database(drop_existing)

            st.session_state.db_message = (
                "Equity database created successfully!"
            )

        except Exception as e:
            log(f"Database creation failed: {e}", level="error")
            st.session_state.db_message = f"ERROR {e}"
            raise
    action_button(
        "Create Equity Database",
        task
    )
    
# --------------------------------------------------------------------------
def operation_refresh_symbols():
    def task():
        try:
            clear_log()
            log("Starting full symbol refresh")
            refresh_symbols()
            st.session_state.db_message = "Symbol refresh completed successfully"
        except Exception as e:
            log(f"Symbol refresh failed: {e}", level="error")
            st.session_state.db_message = f"ERROR {e}"
            raise

    action_button(
        "Refresh Symbols",
        task
    )
    
# --------------------------------------------------------------------------
def operation_update_calendar():
    def task():
        try:
            clear_log()
            upsert_nse_holidays()
            st.session_state.db_message = "Exchange holidays updated successfully"
        except Exception as e:
            st.session_state.db_message = f"ERROR {e}"
    action_button(
        "Update Exchange Calendar",
        task
    )
    
# --------------------------------------------------------------------------
def handle_database_operations():
    st.subheader("Database operations")
    st.caption("Choose an operation below. Each action runs when you click its button.")

    message_placeholder = st.empty()

    with st.container(border=True):
        st.subheader("Initialize equity database")
        st.caption("Create the required equity database tables and indexes.")
        operation_create_database()

    with st.container(border=True):
        st.subheader("Refresh symbols")
        st.caption("Refresh the market symbols used by the application.")
        operation_refresh_symbols()

    with st.container(border=True):
        st.subheader("Update NSE calendar")
        st.caption("Synchronize the NSE exchange holiday calendar.")
        operation_update_calendar()

    with message_placeholder.container():
        show_message("db_message")
# --------------------------------------------------------------------------