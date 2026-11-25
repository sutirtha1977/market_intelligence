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
# Description on the left, action on the right. Every card uses the same
# split, so all buttons share one position and width.
CARD_COLUMNS = [3.2, 1.2]

# Any column that contains the .btn-col marker gets full-width, equal-height
# buttons, whatever markup action_button produces.
CARD_STYLE = """
<style>
[data-testid="stColumn"]:has(.btn-col) [data-testid="stElementContainer"],
[data-testid="stColumn"]:has(.btn-col) [data-testid="stButton"],
[data-testid="stColumn"]:has(.btn-col) .stButton,
[data-testid="stColumn"]:has(.btn-col) div:has(> button) {
    width: 100% !important;
}
[data-testid="stColumn"]:has(.btn-col) button {
    width: 100% !important;
    min-width: 100% !important;
    height: 2.75rem;
    justify-content: center;
    white-space: nowrap;
}
[data-testid="stElementContainer"]:has(.btn-col) {
    display: none;
}
</style>
"""


def button_column_marker() -> None:
    st.markdown('<span class="btn-col"></span>', unsafe_allow_html=True)
# --------------------------------------------------------------------------
def card_header(title: str, description: str) -> None:
    st.markdown(f"**{title}**")
    st.caption(description)
# --------------------------------------------------------------------------
def operation_create_database(options_slot):
    with options_slot:
        drop_existing = st.checkbox(
            "Drop existing tables",
            key="db_drop_existing",
            help="Deletes every existing table and all of its data before recreating the schema."
        )
        if drop_existing:
            st.warning(
                "All existing tables and their data will be permanently deleted.",
                icon=":material/warning:"
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
    st.markdown(CARD_STYLE, unsafe_allow_html=True)

    # st.subheader("Database operations")
    # st.caption("Set up the database and keep reference data current.")

    message_placeholder = st.empty()

    st.markdown("##### Setup")
    with st.container(border=True):
        text_col, action_col = st.columns(CARD_COLUMNS, vertical_alignment="center")
        with text_col:
            card_header(
                "Initialize equity database",
                "Create the required equity database tables and indexes."
            )
            options_slot = st.container()
        with action_col:
            button_column_marker()
            operation_create_database(options_slot)

    st.markdown("##### Reference data")
    with st.container(border=True):
        text_col, action_col = st.columns(CARD_COLUMNS, vertical_alignment="center")
        with text_col:
            card_header(
                "Symbols",
                "Refresh the market symbols used by the application."
            )
        with action_col:
            button_column_marker()
            operation_refresh_symbols()

    with st.container(border=True):
        text_col, action_col = st.columns(CARD_COLUMNS, vertical_alignment="center")
        with text_col:
            card_header(
                "NSE calendar",
                "Synchronize the NSE exchange holiday calendar."
            )
        with action_col:
            button_column_marker()
            operation_update_calendar()

    with message_placeholder.container():
        show_message("db_message")
# --------------------------------------------------------------------------