
# core/ui_helpers.py

import traceback
from html import escape
from typing import Callable, Optional, Any

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
    clear_logs_before: bool = True,
    transparent_overlay: bool = False
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
    blocker_class = "market-operation-blocker"
    if transparent_overlay:
        blocker_class += " market-operation-blocker-transparent"
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
                .market-operation-blocker-transparent {{
                    background: rgba(15, 23, 42, 0.08);
                    backdrop-filter: none;
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
                <div class="{blocker_class}" aria-hidden="true"></div>
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
