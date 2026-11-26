# operations/scanners/dialog_chart.py

import streamlit as st
import pandas as pd

from core.charts import prepare_stock_chart_figure
from services.equity.yahoo.yahoo_data_service import (
    fetch_asset_data_from_signal_date
)

# --------------------------------------------------------------------------
CHART_DAYS = 365
# --------------------------------------------------------------------------

@st.dialog("Price Chart", width="large")
def show_symbol_dialog(
    symbol,
    symbol_id,
    asset_key,
    signal_date,
    reference_line=None,
    key=None
):

    # =========================================================
    # VALIDATION
    # =========================================================
    asset_key = asset_key or st.session_state.get("current_asset_key")

    if not asset_key:
        st.error("Asset key is missing. Cannot load stock data.")
        return

    if symbol_id is None:
        st.error("symbol_id is missing")
        return

    if signal_date is None:
        st.error("Signal date is missing")
        return

    # =========================================================
    # CLEAN INPUTS
    # =========================================================
    asset_key = str(asset_key)
    symbol_id = int(symbol_id)
    signal_date = pd.to_datetime(signal_date)

    # =========================================================
    # HEADER
    # =========================================================
    st.markdown(
        f"### {symbol} &nbsp;&nbsp;&nbsp; "
        f"<span style='font-size:13px;color:#6B7280;'>"
        f"SIGNAL DATE: {signal_date.strftime('%d %b %Y')}"
        f"</span>",
        unsafe_allow_html=True
    )

    # =========================================================
    # FETCH DATA
    # =========================================================
    df_daily = fetch_asset_data_from_signal_date(
        symbol_id=symbol_id,
        asset_key=asset_key,
        start_date=signal_date,
        days=CHART_DAYS,
        timeframe="1d"
    )

    df_weekly = fetch_asset_data_from_signal_date(
        symbol_id=symbol_id,
        asset_key=asset_key,
        start_date=signal_date,
        days=CHART_DAYS,
        timeframe="1wk"
    )

    # =========================================================
    # EMPTY CHECK
    # =========================================================
    if (
        (df_daily is None or df_daily.empty)
        and
        (df_weekly is None or df_weekly.empty)
    ):
        st.warning("No data available")
        return

    # =========================================================
    # DAILY CHART
    # =========================================================
    if df_daily is not None and not df_daily.empty:


        fig_daily = prepare_stock_chart_figure(
            df_daily,
            "DAILY",
            reference_line=reference_line
        )

        st.plotly_chart(
            fig_daily,
            width="stretch",
            key=f"{key}_daily" if key else None
        )

    else:
        st.info("No daily data available")

    # =========================================================
    # SPACING
    # =========================================================
    st.markdown("<br>", unsafe_allow_html=True)

    # =========================================================
    # WEEKLY CHART
    # =========================================================
    if df_weekly is not None and not df_weekly.empty:


        fig_weekly = prepare_stock_chart_figure(
            df_weekly,
            "WEEKLY",
            reference_line=reference_line
        )

        st.plotly_chart(
            fig_weekly,
            width="stretch",
            key=f"{key}_weekly" if key else None
        )

    else:
        st.info("No weekly data available")

# --------------------------------------------------------------------------