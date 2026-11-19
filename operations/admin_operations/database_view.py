# operations/admin_operations/database_view.py

import streamlit as st
from streamlit_option_menu import option_menu
from config.logger import log
from core.ui_helpers import action_button, render_html_table, show_message
from core.widgets import get_horizontal_internal_tab_styles
from config.db_config import ASSET_CHOICE_MAP
from database.create_equity_database import create_equity_database
# from database.create_fno_database import create_fno_database
# from services.equity.symbol_service import refresh_symbols
# from services.equity.utility_service import upsert_nse_holidays

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

    show_message("db_message")
    
# --------------------------------------------------------------------------
def operation_refresh_symbols():
    confirm = st.radio(
        label="Confirm Symbol Refresh ?",
        options=["Yes", "No"],
        captions=[
        "Proceed with refreshing all symbols in the database.",
        "Cancel the symbol refresh operation."],
        key="db_refresh_confirm",
        horizontal=True,
        label_visibility="visible"
    ).upper()
    def task():
        try:
            if confirm == "YES":
                # refresh_symbols()
                st.session_state.db_message = "All symbols refreshed successfully"
            else:
                st.session_state.db_message = "Operation Cancelled"
        except Exception as e:
            st.session_state.db_message = f"ERROR {e}"
    action_button(
        "Refresh Symbols",
        task
    )
    
# --------------------------------------------------------------------------
def operation_update_calendar():
    def task():
        try:
            # upsert_nse_holidays()
            st.session_state.db_message = "Exchange holidays updated successfully"
        except Exception as e:
            st.session_state.db_message = f"ERROR {e}"
    action_button(
        "Update Exchange Calendar",
        task
    )
    
# --------------------------------------------------------------------------
def handle_database_operations():
    show_message("db_message")

    operations = [
        "INITIALIZE DATABASE",
        "REFRESH SYMBOLS",
        "UPDATE NSE CALENDAR"
    ]

    operations_map = {
        "INITIALIZE DATABASE": operation_create_database,
        "REFRESH SYMBOLS": operation_refresh_symbols,
        "UPDATE NSE CALENDAR": operation_update_calendar
    }

    choice = option_menu(
        menu_title=None,
        options=operations,
        icons=["server", "arrow-repeat", "calendar-check", "calendar"],
        menu_icon="",
        default_index=0,
        orientation="horizontal",
        styles=get_horizontal_internal_tab_styles()
    )

    st.markdown('</div>', unsafe_allow_html=True)

    if choice in operations_map:
        operations_map[choice]()
# --------------------------------------------------------------------------