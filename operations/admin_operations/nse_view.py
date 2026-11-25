# operations/admin_operations/nse_view.py
#
# Option B: pipeline board.
# Every daily step is visible at once with its own status, and the whole
# routine can be run in order with a single button.

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import date, datetime
from typing import Callable, Optional

import streamlit as st
from streamlit.delta_generator import DeltaGenerator

from config.logger import log, clear_log
from core.ui_helpers import action_button

ProgressCallback = Callable[[str, int, int], None]

# {operation_key: {"ok": bool, "message": str, "finished_at": datetime, "seconds": float}}
st.session_state.setdefault("nse_runs", {})
st.session_state.setdefault("nse_summary", None)
st.session_state.setdefault("nse_progress", None)

# One column layout shared by the header row and every operation row, so the
# button column has the same left edge and width everywhere.
# [icon, title + description, status, button]
ROW_COLUMNS = [0.5, 4, 2.4, 1.6]

# Makes every button inside the tabs fill its column, so all buttons share one
# width regardless of label length.
BUTTON_STYLE = """
<style>
[data-testid="stTabs"] .stElementContainer:has(.stButton),
[data-testid="stTabs"] .stButton {
    width: 100% !important;
}
[data-testid="stTabs"] .stButton > button {
    width: 100% !important;
    min-height: 2.5rem;
    white-space: nowrap;
}
</style>
"""


# ---------------------------------------------------------------------------
# Runners (lazy imports keep the page fast to load)
# ---------------------------------------------------------------------------

def _sync_constituents(_=None) -> None:
    from services.index.nse_data_service import upsert_nifty_index_constituents
    upsert_nifty_index_constituents()


def _load_history(_=None) -> None:
    from services.index.nse_data_service import upsert_nse_index_history
    upsert_nse_index_history()


def _update_incremental(_=None) -> None:
    from services.index.nse_data_service import upsert_nse_index_incremental
    upsert_nse_index_incremental()


def _update_weekly_monthly(progress: Optional[ProgressCallback] = None) -> None:
    from services.index.nse_data_service import update_weekly_monthly_for_all_symbols
    update_weekly_monthly_for_all_symbols(
        asset_type="nse_india_index", progress_callback=progress
    )


def _refresh_indicators(progress: Optional[ProgressCallback] = None) -> None:
    from services.equity.indicator.indicator_engine import refresh_indicators
    refresh_indicators(asset_types=["nse_india_index"], progress_callback=progress)


def _update_srt(_=None) -> None:
    from services.index.nse_data_service import update_nse_index_srt
    update_nse_index_srt()


def _update_vix(_=None) -> None:
    from services.index.vix_service import update_vix_daily_data
    update_vix_daily_data()


def _compute_vix_features(_=None) -> None:
    from services.index.vix_service import compute_vix_features_talib
    compute_vix_features_talib()


@dataclass(frozen=True)
class Operation:
    key: str
    title: str
    description: str
    button: str
    run: Callable
    log_message: str
    progress_label: Optional[str] = None


# Order matters: later steps depend on earlier ones.
DAILY = [
    Operation("incremental", "Index prices",
              "Fetch the latest daily prices and append them.",
              "Update prices", _update_incremental, "Updating incremental data"),
    Operation("weekly_monthly", "Weekly & monthly bars",
              "Aggregate daily prices into weekly and monthly bars.",
              "Update bars", _update_weekly_monthly, "Updating weekly/monthly data",
              progress_label="Weekly/monthly"),
    Operation("indicators", "Indicators",
              "Recalculate technical indicators for every index.",
              "Update indicators", _refresh_indicators, "Refreshing indicators",
              progress_label="Indicators"),
    Operation("srt", "Daily SRT",
              "Recompute the daily SRT values.",
              "Update SRT", _update_srt, "Updating daily SRT for index"),
    Operation("vix_prices", "VIX prices",
              "Fetch the latest India VIX daily prices.",
              "Update VIX", _update_vix, "Starting VIX daily update"),
    Operation("vix_features", "VIX features",
              "Calculate VIX features with TA-Lib.",
              "Update features", _compute_vix_features, "Starting VIX feature computation (TA-Lib)"),
]

ONE_TIME = [
    Operation("constituents", "Index constituents",
              "Load the current constituents of each NIFTY index. Run when composition changes.",
              "Sync indices", _sync_constituents, "Updating index constituents"),
    Operation("history", "Historical prices",
              "Backfill full price history for all indices. Run on setup or after a reset.",
              "Load history", _load_history, "Loading historical data"),
]


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------

def _execute(op: Operation, area: DeltaGenerator) -> bool:
    """Run one operation inside `area`, record the result, return success."""
    started = time.perf_counter()
    slot = area.empty()
    bar: Optional[DeltaGenerator] = None
    try:
        clear_log()
        log(op.log_message)

        callback: Optional[ProgressCallback] = None
        if op.progress_label:
            progress_bar = slot.progress(0.0, text=f"{op.title}: preparing...")
            bar = progress_bar
            st.session_state.nse_progress = (0.0, f"{op.title}: preparing...")

            def update_progress(timeframe: str, completed: int, total: int) -> None:
                fraction = completed / total if total else 1.0
                fraction = min(max(fraction, 0.0), 1.0)
                text = f"{op.title} · {timeframe}: {completed} of {total}"
                st.session_state.nse_progress = (fraction, text)
                progress_bar.progress(
                    fraction,
                    text=text,
                )
            callback = update_progress
        else:
            slot.caption(f"{op.title}: running...")

        op.run(callback)
        if bar is not None:
            text = f"{op.title}: complete"
            st.session_state.nse_progress = (1.0, text)
            bar.progress(1.0, text=text)
        ok, message = True, ""
    except Exception as exc:
        log(f"ERROR: {exc}", level="error")
        ok, message = False, str(exc)
        if bar is not None:
            progress, _ = st.session_state.nse_progress or (0.0, "")
            text = f"{op.title}: failed"
            st.session_state.nse_progress = (progress, text)
            bar.progress(progress, text=text)

    st.session_state.nse_runs[op.key] = {
        "ok": ok,
        "message": message,
        "finished_at": datetime.now(),
        "seconds": time.perf_counter() - started,
    }
    return ok


def _run_sequence(ops: list[Operation], area: DeltaGenerator) -> None:
    """Run steps in order and stop at the first failure."""
    with area.status("Running daily update", expanded=True) as status:
        failed: Optional[Operation] = None
        for index, op in enumerate(ops, start=1):
            status.update(label=f"Step {index} of {len(ops)}: {op.title}")
            if not _execute(op, status):
                failed = op
                break

        if failed:
            error = st.session_state.nse_runs[failed.key]["message"]
            status.update(label=f"Stopped at {failed.title}", state="error")
            st.session_state.nse_summary = (
                "error", f"Daily update stopped at {failed.title}: {error}"
            )
        else:
            status.update(label="Daily update complete", state="complete", expanded=False)
            st.session_state.nse_summary = (
                "success", f"All {len(ops)} daily steps completed."
            )


def _run_single_operation(op: Operation, area: DeltaGenerator) -> bool:
    st.session_state.nse_summary = None
    st.session_state.nse_progress = None
    ok = _execute(op, area)
    if ok:
        st.session_state.nse_summary = ("success", f"{op.title} updated.")
    else:
        error = st.session_state.nse_runs[op.key]["message"]
        st.session_state.nse_summary = ("error", f"{op.title} failed: {error}")
    return ok


def _run_all_daily_operations(area: DeltaGenerator) -> bool:
    st.session_state.nse_summary = None
    st.session_state.nse_progress = None
    _run_sequence(list(DAILY), area)
    return True


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def _state_of(op: Operation) -> str:
    run = st.session_state.nse_runs.get(op.key)
    if not run:
        return "idle"
    if not run["ok"]:
        return "failed"
    return "done" if run["finished_at"].date() == date.today() else "idle"


STATE_ICON = {
    "done": ":green[:material/check_circle:]",
    "failed": ":red[:material/error:]",
    "idle": ":gray[:material/radio_button_unchecked:]",
}


def _status_text(op: Operation) -> str:
    run = st.session_state.nse_runs.get(op.key)
    state = _state_of(op)
    if state == "idle" and not run:
        return "Not run this session"
    if state == "idle":
        return f"Last run {run['finished_at']:%d %b, %H:%M}"
    label = "Updated" if state == "done" else "Failed"
    return f"{label} {run['finished_at']:%H:%M} · {run['seconds']:.1f}s"


def _render_row(op: Operation, area: DeltaGenerator) -> None:
    """Draw one operation row and run it behind the transparent blocker."""
    with st.container(border=True):
        icon_col, text_col, status_col, action_col = st.columns(
            ROW_COLUMNS, vertical_alignment="center"
        )
        icon_col.markdown(f"### {STATE_ICON[_state_of(op)]}")
        text_col.markdown(f"**{op.title}**")
        text_col.caption(op.description)
        status_col.caption(_status_text(op))
        with action_col:
            result = action_button(
                op.button,
                lambda: _run_single_operation(op, area),
                clear_logs_before=False,
                transparent_overlay=True,
            )
        if result is not None:
            st.rerun()

        run = st.session_state.nse_runs.get(op.key)
        if run and not run["ok"]:
            with st.expander("Error details"):
                st.code(run["message"], language=None)


def _render_summary_metrics() -> None:
    done = sum(_state_of(op) == "done" for op in DAILY)
    failed = sum(_state_of(op) == "failed" for op in DAILY)
    times = [
        r["finished_at"]
        for op in DAILY
        if (r := st.session_state.nse_runs.get(op.key))
    ]
    last = max(times) if times else None

    m1, m2, m3 = st.columns(3)
    m1.metric("Daily steps updated today", f"{done} of {len(DAILY)}")
    m2.metric("Failed", failed)
    m3.metric("Last activity", f"{last:%H:%M}" if last else "None yet")


def handle_nse_operations() -> None:
    # st.subheader("NSE index data")
    # st.caption("Update index prices, indicators and VIX data.")

    st.markdown(BUTTON_STYLE, unsafe_allow_html=True)

    _render_summary_metrics()

    summary = st.session_state.nse_summary
    if summary:
        (st.success if summary[0] == "success" else st.error)(summary[1])

    # Progress for any run appears here, above the lists.
    run_area = st.container()

    daily_tab, one_time_tab = st.tabs(["Daily update", "One-time setup"])

    with daily_tab:
        # Same columns as the rows below, so "Run all steps" sits directly
        # above the row buttons with the same width.
        _, head, _, action = st.columns(ROW_COLUMNS, vertical_alignment="center")
        head.caption("Steps run top to bottom. Each step needs the one before it.")
        with action:
            result = action_button(
                "Run all steps",
                lambda: _run_all_daily_operations(run_area),
                clear_logs_before=False,
                transparent_overlay=True,
            )
        if result is not None:
            st.rerun()

        for op in DAILY:
            _render_row(op, run_area)

    with one_time_tab:
        st.caption("Setup and backfill tasks. These are rarely needed.")
        for op in ONE_TIME:
            _render_row(op, run_area)

    if st.session_state.nse_progress:
        progress, text = st.session_state.nse_progress
        run_area.progress(progress, text=text)