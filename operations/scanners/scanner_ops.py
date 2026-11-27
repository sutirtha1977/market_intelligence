
# operations/scanners/scanner_ops.py

from dataclasses import dataclass
from datetime import datetime
from functools import partial
from typing import Any, Callable

import pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu

from config.db_config import ASSET_CHOICE_MAP
from core.ui_helpers import action_button
from core.widgets import (
    get_horizontal_internal_tab_styles,
    style_selectbox,
)

from services.scanners.scanner_weekly.scanner_weekly import scanner_weekly
from services.scanners.backtest_momentum.scanner_service_momentum import (
    scanner_backtest_momentum,
)
from services.scanners.backtest_future_breakdown.scanner_service_future_breakdown import (
    scanner_backtest_future_breakdown,
)


# --------------------------------------------------------------------------
# STYLE
# --------------------------------------------------------------------------

PAGE_STYLE = """
<style>
[data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .btn-col)
    [data-testid="stElementContainer"],
[data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .btn-col)
    [data-testid="stButton"] {
    width: 100% !important;
}

[data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .btn-col)
    button:not([data-testid^="stNumberInputStep"]) {
    width: 100% !important;
    height: 2.75rem;
    justify-content: center;
    white-space: nowrap;
}

[data-testid="stElementContainer"]:has(.btn-col) {
    display: none;
}
</style>
"""


# --------------------------------------------------------------------------
# PARAMETERS
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Param:
    """Defines a scanner parameter and its Streamlit widget."""

    key: str
    label: str
    build: Callable[[str, str], Any]


def asset_param(weekly_only: bool = False) -> Param:
    """
    Create the asset selection parameter.

    Weekly scanner:
        Uses only the first ASSET_CHOICE_MAP option.

    Other scanners:
        Use all ASSET_CHOICE_MAP options.
    """

    def build(label: str, key: str):
        choices = (
            list(ASSET_CHOICE_MAP)[:1]
            if weekly_only
            else list(ASSET_CHOICE_MAP)
        )

        choice = st.selectbox(
            label,
            choices,
            key=key,
        )

        return ASSET_CHOICE_MAP[choice]

    return Param(
        key="asset_type",
        label="Asset type",
        build=build,
    )


def start_year_param() -> Param:

    def build(label: str, key: str):
        current_year = datetime.now().year

        return int(
            st.number_input(
                label,
                min_value=2000,
                max_value=current_year,
                value=current_year,
                key=key,
                help="First year of the scan.",
            )
        )

    return Param(
        key="start_year",
        label="Start year",
        build=build,
    )


def lookback_param(default: int = 20) -> Param:

    def build(label: str, key: str):
        return int(
            st.number_input(
                label,
                min_value=1,
                max_value=20,
                value=default,
                key=key,
                help="How many years of history each signal looks back over.",
            )
        )

    return Param(
        key="lookback_years",
        label="Lookback years",
        build=build,
    )


def scanner_params(weekly_only: bool = False) -> tuple[Param, ...]:
    """
    Return the parameter configuration for a scanner.

    Set weekly_only=True to restrict the asset selection
    to the first ASSET_CHOICE_MAP option.
    """

    return (
        asset_param(weekly_only=weekly_only),
        start_year_param(),
        lookback_param(),
    )


# --------------------------------------------------------------------------
# SCANNERS
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Scanner:
    key: str
    title: str
    icon: str
    description: str
    params: tuple[Param, ...]
    run: Callable[..., Any]
    button: str
    conditions: tuple[str, ...] = ()

    @property
    def results_key(self) -> str:
        return f"scanner_{self.key}_results"


SCANNERS = (
    Scanner(
        key="weekly",
        title="Weekly scanner",
        icon="calendar-week",
        description="Weekly trend and relative strength setup.",
        params=scanner_params(weekly_only=True),
        run=scanner_weekly,
        button="Run Weekly Scanner",
        conditions=(
            "Relative Strength (RS) > 0",
            "Relative Strength (RS) > RS Moving Average",
            "Weekly Close ≥ 100 (India equities only)",
            "Weekly Close > SMA(20)",
            "Weekly Low ≤ Lowest Low of Previous 4 Weeks",
            "SMA(20) is rising (Current SMA > SMA 2 Weeks Ago)",
            "Weekly Close ≥ Previous Week Close",
            "RSI(3) > RSI(9)",
            "RSI(9) > EMA(RSI(9), 3)",
            "EMA(RSI(9), 3) > WMA(RSI(9), 21)",
            "Weekly RSI(3) > 50",
            "Monthly RSI(3) > 50",
        ),
    ),

    Scanner(
        key="momentum",
        title="Momentum scanner",
        icon="speedometer2",
        description="Momentum setup.",
        params=scanner_params(),
        run=partial(
            scanner_backtest_momentum,
            scanner_name="momentum",
        ),
        button="Run Momentum Scanner",
    ),

    Scanner(
        key="future_breakdown",
        title="Future breakdown",
        icon="graph-down-arrow",
        description="Future breakdown setup.",
        params=scanner_params(),
        run=partial(
            scanner_backtest_future_breakdown,
            scanner_name="future_breakdown",
        ),
        button="Run Future Breakdown",
    ),
)


# --------------------------------------------------------------------------
# SESSION STATE
# --------------------------------------------------------------------------

for _scanner in SCANNERS:
    st.session_state.setdefault(_scanner.results_key, None)

st.session_state.setdefault("scanner_backtest_message", None)


# --------------------------------------------------------------------------
# RESULTS
# --------------------------------------------------------------------------

DATE_COLUMNS = ("signal_date", "Date")


def _signals_frame(data: Any) -> pd.DataFrame | None:
    """
    Normalize scanner output into a DataFrame.

    Supports:
        DataFrame
        Tuple (backtest_df, display_df)

    For tuple results, the second element is displayed.
    """

    if isinstance(data, tuple):
        if len(data) > 1:
            return data[1]

        return data[0] if data else None

    return data


def _prepare_signals(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, str | None]:
    """
    Clean column names, parse the date column and sort by date.
    """

    table = df.copy()

    table.columns = [
        str(col).strip()
        for col in table.columns
    ]

    date_col = next(
        (col for col in DATE_COLUMNS if col in table.columns),
        None,
    )

    if date_col:
        table[date_col] = pd.to_datetime(
            table[date_col].astype(str).str.strip(),
            format="%d-%b-%Y",
            errors="coerce",
        )

        table = (
            table.sort_values(
                by=date_col,
                ascending=True,
                kind="stable",
            )
            .reset_index(drop=True)
        )

    return table, date_col


def render_results(scanner: Scanner) -> None:
    """
    Display scanner results as a standard, non-interactive dataframe.
    """

    st.markdown("##### Current year signals")

    data = st.session_state.get(scanner.results_key)

    if data is None:
        st.caption(
            "Set the parameters and run the scanner to see signals here."
        )
        return

    df = _signals_frame(data)

    if not isinstance(df, pd.DataFrame) or df.empty:
        st.info("The scan returned no signals.")
        return

    try:
        table, date_col = _prepare_signals(df)

        st.caption(f"{len(table):,} signals")

        column_config = (
            {
                date_col: st.column_config.DateColumn(
                    date_col,
                    format="DD-MMM-YYYY",
                )
            }
            if date_col
            else None
        )

        st.dataframe(
            table,
            width="stretch",
            hide_index=True,
            column_config=column_config,
        )

    except Exception as e:
        st.error(f"Could not prepare the signals table: {e}")


# --------------------------------------------------------------------------
# PAGE
# --------------------------------------------------------------------------

def render_scanner(scanner: Scanner) -> None:
    """
    Render scanner parameters on the left and results on the right.
    """

    params_col, results_col = st.columns(
        [1.1, 3],
        gap="medium",
    )

    with params_col, st.container(border=True):

        values = {
            param.key: param.build(
                param.label,
                f"{scanner.key}_{param.key}",
            )
            for param in scanner.params
        }

        if scanner.conditions:
            with st.expander("Scanner conditions"):
                st.markdown(
                    "\n".join(
                        f"- {condition}"
                        for condition in scanner.conditions
                    )
                )

        def task():
            st.session_state[scanner.results_key] = scanner.run(
                **values
            )

            st.session_state.scanner_backtest_message = (
                f"{scanner.title} completed"
            )

        st.divider()

        with st.container():
            st.markdown(
                '<span class="btn-col"></span>',
                unsafe_allow_html=True,
            )

            action_button(
                scanner.button,
                task,
            )

    with results_col, st.container(border=True):
        render_results(scanner)


# --------------------------------------------------------------------------
# MAIN HANDLER
# --------------------------------------------------------------------------

def handle_scanner_backtest_operations():

    style_selectbox()

    st.markdown(
        PAGE_STYLE,
        unsafe_allow_html=True,
    )

    choice = option_menu(
        menu_title=None,
        options=[scanner.title for scanner in SCANNERS],
        icons=[scanner.icon for scanner in SCANNERS],
        menu_icon="clipboard-data",
        default_index=0,
        orientation="horizontal",
        styles=get_horizontal_internal_tab_styles(),
    )

    selected_scanner = next(
        scanner
        for scanner in SCANNERS
        if scanner.title == choice
    )

    render_scanner(selected_scanner)
