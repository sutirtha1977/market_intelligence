# operations/home_dashboard/home_view.py

import streamlit as st


# IMPORTANT: delay imports (lazy loading)
def load_styles():
    from operations.home_dashboard.home_ops.home_styles import inject_home_styles
    inject_home_styles()

def load_header(progress_placeholder):
    from operations.home_dashboard.home_ops.market_ops import handle_header_section
    handle_header_section(progress_placeholder)

def load_srt():
    from operations.home_dashboard.home_ops.srt_ops import handle_srt_section
    handle_srt_section()

def load_news():
    from operations.home_dashboard.home_ops.news_ops import handle_news_section
    handle_news_section()


# ----------------------------------------------------------
# STATE
# ----------------------------------------------------------
if "busy" not in st.session_state:
    st.session_state.busy = False


# ----------------------------------------------------------
# MAIN
# ----------------------------------------------------------
def handle_home_operations():
    # UI styles (keep lightweight)
    load_styles()
    # ----------------------------------------------------------
    # FAST ROUTER
    # ----------------------------------------------------------
    with st.spinner("Loading market data...", show_time=True):
        load_header(None)
    load_srt()
    load_news()