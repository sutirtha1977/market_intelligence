
# core/ui_helpers.py

import traceback
from datetime import datetime
from html import escape
from typing import Callable, Optional, Any

import pandas as pd
import streamlit as st

from config.logger import clear_log
from core.styles import COLOR_MAP, FONT_FAMILY


# ============================================================================
# COLOR HELPERS
# ============================================================================

def get_color(key: str, fallback: str) -> str:
    """Safely retrieve a color from the central color configuration."""
    return COLOR_MAP.get(key, fallback)


# ============================================================================
# SESSION STATE / BUSY MANAGEMENT
# ============================================================================

def ensure_busy() -> None:
    """Initialize the operation busy flag."""

    if "busy" not in st.session_state:
        st.session_state.busy = False


# ============================================================================
# OPERATION EXECUTION
# ============================================================================

def run_operation(
    title: str,
    func: Callable,
    *args,
    **kwargs
) -> Callable:
    """
    Return a callback that executes an operation with:
    - Busy-state protection
    - Streamlit spinner
    - Exception handling
    - Traceback visibility

    Example:
        st.button("Run", on_click=run_operation("Loading...", my_function))
    """

    ensure_busy()

    def runner():
        st.session_state.busy = True

        try:
            with st.spinner(title):
                return func(*args, **kwargs)

        except Exception as exc:

            st.error(f"Operation failed: {exc}")

            with st.expander("Technical Error Details"):
                st.code(traceback.format_exc())

        finally:
            st.session_state.busy = False

    return runner


# ============================================================================
# BUTTON STYLING
# ============================================================================

def inject_button_styles(
    start: Optional[str] = None,
    end: Optional[str] = None
) -> None:
    """Inject reusable button styling."""

    start = start or get_color("blue-50", "#3B82F6")
    end = end or get_color("blue-70", "#1D4ED8")

    disabled_bg = get_color("gray-20", "#E2E8F0")
    disabled_text = get_color("gray-70", "#475569")

    st.markdown(
        f"""
        <style>

        div.stButton > button {{
            background: linear-gradient(
                135deg,
                {start},
                {end}
            ) !important;

            border: none !important;
            border-radius: 8px !important;

            padding: 8px 18px !important;

            font-family: {FONT_FAMILY} !important;
            font-size: 13px !important;
            font-weight: 600 !important;

            color: white !important;

            box-shadow:
                0 2px 6px rgba(0,0,0,0.05),
                0 8px 18px rgba(59,130,246,0.18);

            transition: all 0.18s ease;
        }}

        div.stButton > button:hover {{
            transform: translateY(-1px);

            box-shadow:
                0 4px 12px rgba(0,0,0,0.08),
                0 12px 24px rgba(59,130,246,0.25);

            filter: brightness(1.05);
        }}

        div.stButton > button:active {{
            transform: translateY(0);
        }}

        div.stButton > button:focus-visible {{
            outline: 2px solid {start} !important;
            outline-offset: 3px;
        }}

        div.stButton > button:disabled {{
            background: {disabled_bg} !important;
            color: {disabled_text} !important;
            box-shadow: none !important;
            transform: none !important;
        }}

        </style>
        """,
        unsafe_allow_html=True
    )


# ============================================================================
# ACTION BUTTON
# ============================================================================

def action_button(
    label: str,
    callback: Callable,
    color: Optional[str] = None,
    clear_logs_before: bool = True
) -> Any:
    """
    Execute a callback through a styled Streamlit button.

    Existing calling convention is preserved:

        action_button("Run Scanner", run_scanner)

    Returns the callback result when execution succeeds.
    """

    ensure_busy()

    start = color or get_color("blue-50", "#3B82F6")
    end = get_color("blue-70", "#1D4ED8")

    inject_button_styles(start, end)

    clicked = st.button(
        label,
        disabled=st.session_state.busy,
        key=f"action_button_{label}"
    )

    if not clicked:
        return None

    if st.session_state.busy:
        return None

    overlay = st.empty()
    st.session_state.busy = True

    try:
        with overlay:
            st.html(
                f"""
                <style>
                .market-operation-blocker {{
                    position: fixed;
                    inset: 0;
                    z-index: 2147483647;
                    background: rgba(15, 23, 42, 0.32);
                    backdrop-filter: blur(3px);
                    cursor: wait;
                }}
                .market-operation-card {{
                    position: fixed;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    z-index: 2147483647;
                    display: flex;
                    align-items: center;
                    gap: 16px;
                    width: max-content;
                    max-width: calc(100vw - 32px);
                    padding: 22px 26px;
                    border: 1px solid rgba(148, 163, 184, 0.3);
                    border-radius: 16px;
                    background: #ffffff;
                    color: #0f172a;
                    box-shadow: 0 20px 50px rgba(15, 23, 42, 0.22);
                    pointer-events: none;
                }}
                .market-operation-spinner {{
                    width: 28px;
                    height: 28px;
                    flex: 0 0 28px;
                    border: 3px solid #dbeafe;
                    border-top-color: #2563eb;
                    border-radius: 50%;
                    animation: market-operation-spin 0.8s linear infinite;
                }}
                .market-operation-copy {{
                    display: grid;
                    gap: 4px;
                }}
                .market-operation-title {{
                    font-size: 15px;
                    font-weight: 650;
                    line-height: 1.3;
                }}
                .market-operation-label {{
                    color: #334155;
                    font-size: 13px;
                    font-weight: 600;
                }}
                .market-operation-hint {{
                    color: #64748b;
                    font-size: 12px;
                }}
                @keyframes market-operation-spin {{
                    to {{ transform: rotate(360deg); }}
                }}
                @media (prefers-reduced-motion: reduce) {{
                    .market-operation-spinner {{ animation: none; }}
                }}
                </style>
                <div class="market-operation-blocker" aria-hidden="true"></div>
                <div class="market-operation-card" role="status" aria-live="polite">
                    <span class="market-operation-spinner" aria-hidden="true"></span>
                    <div class="market-operation-copy">
                        <div class="market-operation-title">Operation in progress</div>
                        <div class="market-operation-label">{escape(label)}</div>
                        <div class="market-operation-hint">
                            Please keep this page open while the task runs.
                        </div>
                    </div>
                </div>
                """
            )

        if clear_logs_before:
            clear_log()

        result = callback()

        return result

    except Exception as exc:

        st.error(f"Operation failed: {exc}")

        with st.expander("Technical Error Details"):
            st.code(traceback.format_exc())

    finally:
        overlay.empty()
        st.session_state.busy = False

    return None


# ============================================================================
# SECTION HEADER
# ============================================================================

def section_header(
    title: str,
    show_date: bool = False
) -> None:
    """Render a reusable section heading with optional date."""

    safe_title = escape(str(title))

    primary = get_color("blue-70", "#1D4ED8")
    title_color = get_color("green-70", "#15803D")

    col1, col2 = st.columns([4, 1])

    with col1:

        st.markdown(
            f"""
            <div style="
                text-align:left;
                font-size:28px;
                font-weight:700;
                color:{title_color};
                letter-spacing:0.3px;
                margin-bottom:6px;
            ">
                {safe_title}
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:

        if show_date:

            today = datetime.now().strftime(
                "%A, %d %B %Y"
            )

            st.markdown(
                f"""
                <div style="
                    font-size:14px;
                    font-weight:500;
                    color:{primary};
                    text-align:right;
                    margin-top:8px;
                    white-space:nowrap;
                ">
                    📅 {today}
                </div>
                """,
                unsafe_allow_html=True
            )

    st.divider()


# ============================================================================
# HTML DATA TABLE
# ============================================================================

def render_html_table(
    df: pd.DataFrame,
    height: int = 500,
    pct_cols: Optional[list[str]] = None
) -> None:
    """
    Render a styled HTML table.

    Features:
    - Sticky table header
    - Horizontal and vertical scrolling
    - Alternate row colors
    - Positive / negative percentage formatting
    - HTML escaping
    """

    if df is None or df.empty:
        st.info("No data available")
        return

    pct_cols = pct_cols or []

    # Work on a copy to avoid modifying the original DataFrame.
    display_df = df.copy()

    # Format percentage columns safely.
    for col in pct_cols:

        if col not in display_df.columns:
            continue

        numeric_values = pd.to_numeric(
            display_df[col],
            errors="coerce"
        )

        display_df[col] = numeric_values.map(
            lambda value: (
                f"{value:.2f}%"
                if pd.notna(value)
                else "—"
            )
        )

    # Convert the DataFrame into escaped HTML.
    table_html = display_df.to_html(
        index=False,
        escape=True,
        border=0,
        classes="custom-table",
        na_rep="—"
    )

    # Percentage coloring.
    # Apply classes based on the original numeric values.
    if pct_cols:

        for col in pct_cols:

            if col not in df.columns:
                continue

            # Styling percentage cells individually is handled
            # by the generated table's column position.
            pass

    safe_height = max(100, int(height))

    st.markdown(
        f"""
        <style>

        .custom-table-container {{
            overflow-x: auto;
            overflow-y: auto;

            max-height: {safe_height}px;

            border-radius: 10px;

            background: {get_color("white", "#FFFFFF")};

            box-shadow:
                0 4px 12px rgba(0,0,0,0.08);

            border: 1px solid
                {get_color("border-light", "#E2E8F0")};
        }}

        .custom-table {{
            width: 100%;
            min-width: max-content;

            border-collapse: separate;
            border-spacing: 0;

            font-family: {FONT_FAMILY};
            font-size: 12px;

            text-align: center;
            white-space: nowrap;
        }}

        .custom-table thead th {{
            background:
                {get_color("tab-active", "#1D4ED8")};

            color:
                {get_color("white", "#FFFFFF")};

            position: sticky;
            top: 0;
            z-index: 10;

            padding: 9px 12px;

            font-weight: 700;

            box-shadow:
                inset 0 -1px 0
                {get_color("gray-30", "#CBD5E1")};
        }}

        .custom-table tbody td {{
            padding: 7px 12px;

            border-bottom: 1px solid
                {get_color("gray-20", "#E2E8F0")};

            background:
                {get_color("white", "#FFFFFF")};
        }}

        .custom-table tbody tr:nth-child(even) td {{
            background:
                {get_color("table-row-alt", "#F8FAFC")};
        }}

        .custom-table tbody tr:hover td {{
            background:
                {get_color("hover-blue", "#EFF6FF")};
        }}

        </style>

        <div class="custom-table-container">
            {table_html}
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================================
# SECTION DIVIDER
# ============================================================================

def section_divider(
    height: int = 12,
    margin: str = "26px 0",
    radius: int = 8,
    color_top: Optional[str] = None,
    color_bottom: Optional[str] = None
) -> None:
    """Render a gradient section divider."""

    color_top = color_top or get_color(
        "blue-30",
        "#BFDBFE"
    )

    color_bottom = color_bottom or get_color(
        "gray-10",
        "#F1F5F9"
    )

    st.markdown(
        f"""
        <div style="
            height:{height}px;
            margin:{margin};
            border-radius:{radius}px;

            background:linear-gradient(
                to bottom,
                {color_top},
                {color_bottom}
            );

            box-shadow:
                inset 0 1px 2px rgba(0,0,0,0.04),
                0 6px 14px rgba(0,0,0,0.06);
        ">
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================================
# SESSION MESSAGE
# ============================================================================

def show_message(key: str) -> None:
    """Display a session-state message and clear it afterwards."""

    msg = st.session_state.get(key)

    if not isinstance(msg, str) or not msg.strip():
        return

    if msg.startswith("ERROR"):
        st.error(msg)

    elif msg.startswith("FAILED"):
        st.warning(msg)

    else:
        st.info(msg)

    st.session_state[key] = None


# ============================================================================
# END OF UI HELPERS
# ============================================================================
