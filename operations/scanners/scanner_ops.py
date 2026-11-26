# operations/scanners/backtest_ops.py

import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_option_menu import option_menu

from config.db_config import ASSET_CHOICE_MAP
from core.ui_helpers import action_button
from core.widgets import (
    get_horizontal_internal_tab_styles,
    style_selectbox
)
from operations.scanners.dialog_chart import show_symbol_dialog

from services.scanners.backtest_momentum.scanner_service_momentum import (
    scanner_backtest_momentum
)

from services.scanners.backtest_weekly.scanner_service_weekly import (
    scanner_backtest_weekly
)

from services.scanners.backtest_future_breakdown.scanner_service_future_breakdown import (
    scanner_backtest_future_breakdown
)

# --------------------------------------------------------------------------
# SESSION STATE
# --------------------------------------------------------------------------
st.session_state.setdefault("scanner_backtest_message", None)
st.session_state.setdefault("scanner_backtest_weekly_results", None)
st.session_state.setdefault("scanner_backtest_momentum_results", None)
st.session_state.setdefault("scanner_backtest_playground_results", None)
st.session_state.setdefault("scanner_backtest_future_breakdown_results", None)


# --------------------------------------------------------------------------
def render_scanner_inputs(prefix: str, include_target_pct: bool = True):

    column_count = 4 if include_target_pct else 3
    input_columns = st.columns(column_count)
    col1, col2, col3 = input_columns[:3]

    with col1:

        asset_label = st.selectbox(
            "Asset Type",
            options=list(ASSET_CHOICE_MAP.keys())[:2],
            key=f"{prefix}_asset"
        )

        asset_type = ASSET_CHOICE_MAP[asset_label]

    with col2:

        start_year = st.number_input(
            "Start Year",
            min_value=2000,
            max_value=datetime.now().year,
            value=datetime.now().year,
            key=f"{prefix}_start_year"
        )

    with col3:

        lookback_years = st.number_input(
            "Lookback Years",
            min_value=1,
            max_value=20,
            value=2,
            key=f"{prefix}_lookback"
        )

    target_pct = None
    if include_target_pct:
        with input_columns[3]:

            target_pct = st.number_input(
                "Target % Backtest",
                min_value=0.1,
                max_value=50.0,
                value=3.0,
                step=0.1,
                key=f"{prefix}_target"
            )

    return asset_type, start_year, lookback_years, target_pct


# --------------------------------------------------------------------------
def render_scanner_table(results_key: str):

    data = st.session_state.get(results_key)

    if data is None:
        return

    df1 = None
    df2 = None

    # =========================================================
    # UNPACK RESULTS
    # =========================================================
    if isinstance(data, tuple):

        if len(data) > 0:
            df1 = data[0]

        if len(data) > 1:
            df2 = data[1]

    else:

        df1 = data

    # =========================================================
    # BACKTEST RESULTS
    # =========================================================
    if isinstance(df1, pd.DataFrame) and not df1.empty:

        st.markdown("##### Backtest Results")

        st.dataframe(
            df1,
            width="stretch",
            hide_index=True,
            alt="Backtest scanner results"
        )

    # =========================================================
    # CURRENT YEAR SIGNALS
    # =========================================================
    if isinstance(df2, pd.DataFrame) and not df2.empty:

        st.markdown("##### Current Year Signals")

        # =====================================================
        # COPY DATA
        # =====================================================
        df2_display = df2.copy()

        # =====================================================
        # CLEAN COLUMN NAMES
        # =====================================================
        df2_display.columns = [
            str(col).strip()
            for col in df2_display.columns
        ]

        # =====================================================
        # FIND DATE COLUMN
        # =====================================================
        date_col = None

        if "signal_date" in df2_display.columns:
            date_col = "signal_date"

        elif "Date" in df2_display.columns:
            date_col = "Date"

        # =====================================================
        # DATE CONVERSION
        # =====================================================
        if date_col:

            try:

                df2_display[date_col] = (
                    df2_display[date_col]
                    .astype(str)
                    .str.strip()
                )

                df2_display[date_col] = pd.to_datetime(
                    df2_display[date_col],
                    format="%d-%b-%Y",
                    errors="coerce"
                )

            except Exception as e:

                st.error(f"Date conversion failed: {str(e)}")

        # =====================================================
        # SORT
        # =====================================================
        if date_col:

            try:

                df2_display = (
                    df2_display
                    .sort_values(
                        by=date_col,
                        ascending=True,
                        kind="stable"
                    )
                    .reset_index(drop=True)
                )

            except Exception as e:

                st.error(f"Sort failed: {str(e)}")

        # =====================================================
        # DISPLAY TABLE
        # =====================================================
        event = st.dataframe(
            df2_display,
            width="stretch",
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            key=f"symbols_{results_key}",
            alt="Current year scanner signals",

            column_config={
                date_col: st.column_config.DateColumn(
                    date_col,
                    format="DD-MMM-YYYY"
                )
            } if date_col else None
        )

        # =====================================================
        # ROW CLICK
        # =====================================================
        try:

            if event and "selection" in event:

                rows = event["selection"].get("rows", [])

                if rows:

                    idx = rows[0]

                    row = df2_display.iloc[idx]

                    # =================================================
                    # SYMBOL
                    # =================================================
                    symbol = None

                    if "symbol" in row.index:
                        symbol = row["symbol"]

                    elif "Symbol" in row.index:
                        symbol = row["Symbol"]

                    # =================================================
                    # SYMBOL ID
                    # =================================================
                    symbol_id = None

                    if "symbol_id" in row.index:
                        symbol_id = row["symbol_id"]

                    elif "ID" in row.index:
                        symbol_id = row["ID"]

                    # =================================================
                    # SIGNAL DATE
                    # =================================================
                    signal_date = None

                    if "signal_date" in row.index:
                        signal_date = row["signal_date"]

                    elif "Date" in row.index:
                        signal_date = row["Date"]

                    # =================================================
                    # VALUE
                    # =================================================
                    value = None

                    if "weekly_high" in row.index:
                        value = row["weekly_high"]

                    elif "Week High" in row.index:
                        value = row["Week High"]

                    # =================================================
                    # REFERENCE LINE
                    # =================================================
                    reference_line = {
                        "value": value,
                        "label": (
                            f"Weekly High: ({float(value):.2f})"
                            if pd.notna(value)
                            and isinstance(value, (int, float))
                            else "Weekly High"
                        )
                    }

                    asset_key = st.session_state.get(
                        "current_asset_key"
                    )

                    # =================================================
                    # SHOW CHART
                    # =================================================
                    show_symbol_dialog(
                        symbol=symbol,
                        symbol_id=symbol_id,
                        asset_key=asset_key,
                        signal_date=signal_date,
                        reference_line=reference_line
                    )

        except Exception as e:

            st.error(str(e))


# --------------------------------------------------------------------------
def operation_scanner_weekly():

    asset_type, start_year, lookback_years, target_pct = (
        render_scanner_inputs("weekly")
    )
    st.markdown(
        """
        ### Weekly Scanner Conditions
        - Relative Strength (RS) > 0
        - Relative Strength (RS) > RS Moving Average
        - Weekly Close ≥ 100 (India equities only)
        - Weekly Close > SMA(20)
        - Weekly Low ≤ Lowest Low of Previous 4 Weeks
        - SMA(20) is rising (Current SMA > SMA 2 Weeks Ago)
        - Weekly Close ≥ Previous Week Close
        - RSI(3) > RSI(9)
        - RSI(9) > EMA(RSI(9), 3)
        - EMA(RSI(9), 3) > WMA(RSI(9), 21)
        - Weekly RSI(3) > 50
        - Monthly RSI(3) > 50
        """
    )
    
    def task():

        st.session_state["current_asset_key"] = asset_type

        result = scanner_backtest_weekly(
            asset_type=asset_type,
            start_year=int(start_year),
            lookback_years=int(lookback_years),
            target_pct=float(target_pct),
            scanner_name="weekly"
        )

        st.session_state.scanner_backtest_weekly_results = result

        st.session_state.scanner_backtest_message = (
            "Weekly scanner completed"
        )

    action_button(
        "Weekly Backtest",
        task
    )

    render_scanner_table(
        "scanner_backtest_weekly_results"
    )


# --------------------------------------------------------------------------
def operation_scanner_momentum():

    asset_type, start_year, lookback_years, target_pct = (
        render_scanner_inputs("momentum")
    )

    def task():

        st.session_state["current_asset_key"] = asset_type

        result = scanner_backtest_momentum(
            asset_type=asset_type,
            start_year=int(start_year),
            lookback_years=int(lookback_years),
            target_pct=float(target_pct),
            scanner_name="momentum"
        )

        st.session_state.scanner_backtest_momentum_results = result

        st.session_state.scanner_backtest_message = (
            "Momentum scanner completed"
        )

    action_button(
        "Momentum Backtest",
        task
    )

    render_scanner_table(
        "scanner_backtest_momentum_results"
    )

# --------------------------------------------------------------------------
def operation_scanner_future_breakdown():

    asset_type, start_year, lookback_years, _ = (
        render_scanner_inputs(
            "future_breakdown",
            include_target_pct=False
        )
    )

    def task():

        st.session_state["current_asset_key"] = asset_type

        result = scanner_backtest_future_breakdown(
            asset_type=asset_type,
            start_year=int(start_year),
            lookback_years=int(lookback_years),
            scanner_name="future_breakdown"
        )

        st.session_state.scanner_backtest_future_breakdown_results = result

        st.session_state.scanner_backtest_message = (
            "Future Breakdown scanner completed"
        )

    action_button(
        "Future Breakdown",
        task
    )

    render_scanner_table(
        "scanner_backtest_future_breakdown_results"
    )
# --------------------------------------------------------------------------
def handle_scanner_backtest_operations():

    style_selectbox()

    tab_choice = option_menu(
        menu_title=None,
        options=[
            "WEEKLY SCANNER",
            "MOMENTUM SCANNER",
            "FUTURE BREAKDOWN"
        ],
        icons=[
            "calendar-week",
            "speedometer2",
            "graph-down-arrow"
        ],
        menu_icon="clipboard-data",
        default_index=0,
        orientation="horizontal",
        styles=get_horizontal_internal_tab_styles()
    )

    if tab_choice == "WEEKLY SCANNER":

        operation_scanner_weekly()

    elif tab_choice == "MOMENTUM SCANNER":

        operation_scanner_momentum()

    elif tab_choice == "FUTURE BREAKDOWN":

        operation_scanner_future_breakdown()