# operations/admin_operations/admin_ops.py

import streamlit as st
from streamlit_option_menu import option_menu

from core.widgets import (
    get_horizontal_tab_styles,
    style_radio,
    style_selectbox,
    style_inputs
)

# IMPORTANT: delay imports (lazy loading)
def load_yahoo():
    from operations.admin_operations.yahoo_view import handle_yahoo_operations
    handle_yahoo_operations()

def load_nse():
    from operations.admin_operations.nse_view import handle_nse_operations
    handle_nse_operations()

def load_database():
    from operations.admin_operations.database_view import handle_database_operations
    handle_database_operations()


# ----------------------------------------------------------
# STATE
# ----------------------------------------------------------
if "busy" not in st.session_state:
    st.session_state.busy = False


# ----------------------------------------------------------
# MAIN
# ----------------------------------------------------------
def handle_admin_operations():

    # UI styles (keep lightweight)
    style_radio()
    style_selectbox()
    style_inputs()

    # Tabs
    tab_choice = option_menu(
        menu_title=None,
        options=["YAHOO", "NSE", "SCANNERS", "DATABASE"],
        icons=[
            "envelope-fill",
            "bar-chart-line-fill",
            "search-heart",
            "database-fill"
        ],
        menu_icon="gear",
        default_index=0,
        orientation="horizontal",
        styles=get_horizontal_tab_styles()
    )

    # ----------------------------------------------------------
    # FAST ROUTER (NO SPINNER)
    # ----------------------------------------------------------
    if tab_choice == "YAHOO":
        load_yahoo()

    elif tab_choice == "NSE":
        load_nse()

    elif tab_choice == "SCANNERS":
        st.info("Scanners module is under development.")

    elif tab_choice == "DATABASE":
        load_database()