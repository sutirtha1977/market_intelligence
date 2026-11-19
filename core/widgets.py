# core/widgets.py
"""
Reusable widget styling for the analytics app.

* ``get_*_tab_styles``  -> style dicts for streamlit-option-menu (accent aware)
* ``apply_widget_styles`` -> ONE <style> block for selectbox / radio / expander / inputs

Usage (once per run, e.g. in setup_page):
    apply_widget_styles()                  # everything
    apply_widget_styles("radio", "inputs") # only some parts
"""

from functools import lru_cache
from typing import NamedTuple, Optional, Sequence

import streamlit as st

from core.styles import CARD_SHADOW, COLOR_MAP, FONT_FAMILY, FONT_SIZE

__all__ = [
    "Accent",
    "get_horizontal_tab_styles",
    "get_horizontal_internal_tab_styles",
    "get_vertical_tab_styles",
    "apply_widget_styles",
    "style_selectbox",
    "style_radio",
    "apply_expander_style",
    "style_inputs",
]


# ==========================================================
# ACCENT
# ==========================================================

class Accent(NamedTuple):
    main: str
    dark: str
    soft: str
    end: str


DEFAULT_ACCENT = Accent(
    main=COLOR_MAP["blue-60"],
    dark=COLOR_MAP["blue-80"],
    soft=COLOR_MAP["blue-100"],
    end="#38BDF8",
)


def _accent(accent) -> Accent:
    """Accept an Accent, a plain 4-tuple (as in app.SECTION_ACCENTS) or None."""
    return Accent(*accent) if accent else DEFAULT_ACCENT


def _px(value: str, offset: int = 0) -> str:
    """'13px' -> '11px' (offset=-2). Tolerates values like '13'."""
    return f"{int(str(value).lower().replace('px', '').strip()) + offset}px"


# ==========================================================
# OPTION-MENU STYLE DICTS
# ==========================================================
# Note: streamlit-option-menu has no "nav-link:hover" key. Hover colour is set
# with the documented "--hover-color" variable inside "nav-link".

def get_horizontal_tab_styles(font_size: str = FONT_SIZE, accent=None) -> dict:
    a = _accent(accent)

    return {
        "container": {
            "padding": "4px",
            "background": f"linear-gradient(135deg, {COLOR_MAP['gray-10']}, {COLOR_MAP['gray-0']})",
            "border": f"1px solid {COLOR_MAP['border-light']}",
            "border-radius": "12px",
            "box-shadow": CARD_SHADOW,
        },
        "nav": {"gap": "4px"},
        "nav-link": {
            "font-size": _px(font_size, -2),
            "font-family": FONT_FAMILY,
            "font-weight": "500",
            "text-align": "center",
            "color": COLOR_MAP["text-secondary"],
            "background": "transparent",
            "padding": "6px 12px",
            "border-radius": "8px",
            "transition": "all 0.2s ease",
            "--hover-color": a.soft,
        },
        "nav-link-selected": {
            "background": f"linear-gradient(135deg, {a.main}, {a.end})",
            "color": COLOR_MAP["white"],
            "font-weight": "600",
            "box-shadow": f"0 4px 10px {a.main}40",
        },
    }


def get_horizontal_internal_tab_styles(accent=None) -> dict:
    a = _accent(accent)

    return {
        "container": {
            "padding": "1px 0",
            "background": "transparent",
            "border-bottom": f"1px solid {COLOR_MAP['border-light']}",
            "margin-bottom": "8px",
        },
        "nav": {"gap": "12px"},
        "nav-link": {
            "font-size": "12px",
            "font-family": FONT_FAMILY,
            "padding": "4px 2px",
            "border-radius": "0",
            "color": COLOR_MAP["text-secondary"],
            "background": "transparent",
            "border-bottom": "2px solid transparent",
            "transition": "all 0.2s ease",
            "--hover-color": "transparent",
        },
        "nav-link-selected": {
            "color": a.main,
            "font-weight": "600",
            "background": "transparent",
            "border-bottom": f"2px solid {a.main}",
        },
    }


def get_vertical_tab_styles(accent=None) -> dict:
    a = _accent(accent)

    return {
        "container": {"padding": "6px", "background": "transparent"},
        "nav": {"gap": "4px"},
        "nav-link": {
            "font-size": "14px",
            "font-family": FONT_FAMILY,
            "text-align": "left",
            "margin": "4px 0",
            "padding": "10px 14px",
            "color": COLOR_MAP["text-secondary"],
            "border-radius": "10px",
            "background": "transparent",
            "border-left": "3px solid transparent",
            "transition": "all 0.2s ease",
            "--hover-color": a.soft,
        },
        "nav-link-selected": {
            "background": f"linear-gradient(135deg, {a.soft}, {COLOR_MAP['gray-0']})",
            "color": a.dark,
            "font-weight": "600",
            "border-left": f"3px solid {a.main}",
            "box-shadow": CARD_SHADOW,
        },
    }


# ==========================================================
# CSS (colors come from --accent* variables set in app.py)
# ==========================================================

@lru_cache(maxsize=1)
def _css_parts() -> dict:
    C = COLOR_MAP
    acc = "var(--accent, %s)" % DEFAULT_ACCENT.main
    acc_dark = "var(--accent-dark, %s)" % DEFAULT_ACCENT.dark
    acc_soft = "var(--accent-soft, %s)" % DEFAULT_ACCENT.soft

    select = f"""
    div[data-baseweb="select"] > div {{
        border: 1px solid {C['border-light']} !important;
        border-radius: 8px !important;
        background: {C['white']} !important;
        transition: border-color .18s ease, box-shadow .18s ease;
    }}
    div[data-baseweb="select"] > div:hover {{
        border-color: {acc} !important;
    }}
    div[data-baseweb="select"] > div:focus-within {{
        border-color: {acc} !important;
        box-shadow: 0 0 0 3px {acc_soft};
    }}
    div[data-baseweb="select"] span {{
        font-family: {FONT_FAMILY} !important;
        font-size: {FONT_SIZE} !important;
        font-weight: 500;
        color: {C['text-primary']} !important;
    }}
    ul[role="listbox"] {{
        padding: 6px 0;
        border: 1px solid {C['border-light']} !important;
        border-radius: 10px !important;
        background: {C['white']};
        box-shadow: {CARD_SHADOW};
    }}
    li[role="option"] {{
        padding: 8px 14px !important;
        font-family: {FONT_FAMILY} !important;
        font-size: {FONT_SIZE};
        color: {C['text-secondary']};
        border-left: 2px solid transparent;
        transition: background .15s ease, color .15s ease;
    }}
    li[role="option"]:hover {{
        background: {acc_soft} !important;
        color: {acc_dark} !important;
        border-left-color: {acc};
    }}
    li[aria-selected="true"] {{
        background: {acc_soft} !important;
        color: {acc_dark} !important;
        border-left-color: {acc};
        font-weight: 600;
    }}
    ul[role="listbox"]::-webkit-scrollbar {{ width: 6px; }}
    ul[role="listbox"]::-webkit-scrollbar-thumb {{
        background: {C['gray-30']};
        border-radius: 10px;
    }}
    """

    radio = f"""
    [data-testid="stRadio"] div[role="radiogroup"] {{
        display: inline-flex;
        flex-wrap: wrap;
        gap: 6px;
    }}
    [data-testid="stRadio"] label {{
        padding: 4px 12px;
        border: 1px solid {C['border-light']};
        border-radius: 999px;
        background: {C['gray-10']};
        cursor: pointer;
        transition: background .18s ease, border-color .18s ease;
    }}
    [data-testid="stRadio"] label > div:first-child {{ display: none; }}  /* hide the dot */
    [data-testid="stRadio"] label p {{
        font-family: {FONT_FAMILY};
        font-size: 12px;
        font-weight: 500;
        color: {C['text-secondary']};
    }}
    [data-testid="stRadio"] label:hover {{
        background: {C['gray-20']};
    }}
    [data-testid="stRadio"] label:has(input:checked) {{
        border-color: {acc};
        background: {acc_soft};
    }}
    [data-testid="stRadio"] label:has(input:checked) p {{
        color: {acc_dark};
        font-weight: 600;
    }}
    """

    expander = f"""
    [data-testid="stExpander"] {{
        overflow: hidden;
        border: 1px solid {C['border-light']} !important;
        border-left: 4px solid {acc} !important;
        border-radius: 12px !important;
        background: {C['bg-card']} !important;
        box-shadow: {CARD_SHADOW};
    }}
    [data-testid="stExpander"] details summary {{
        padding: .7rem 1rem !important;
        background: linear-gradient(90deg, {acc_soft}, {C['white']}) !important;
        transition: filter .15s ease;
    }}
    [data-testid="stExpander"] details summary:hover {{ filter: brightness(.98); }}
    [data-testid="stExpander"] details summary p {{
        font-weight: 600;
        color: {acc_dark};
    }}
    [data-testid="stExpander"] details summary svg {{ color: {acc} !important; }}
    [data-testid="stExpander"] details > div {{
        padding: 1rem 1.25rem !important;
        background: {C['bg-surface']} !important;
    }}
    """

    inputs = f"""
    [data-baseweb="input"], [data-baseweb="textarea"] {{
        border: 1px solid {C['gray-30']} !important;
        border-radius: 8px !important;
        background: {C['white']} !important;
        transition: border-color .2s ease, box-shadow .2s ease;
    }}
    [data-baseweb="input"]:hover, [data-baseweb="textarea"]:hover {{
        border-color: {C['gray-50']} !important;
    }}
    [data-baseweb="input"]:focus-within, [data-baseweb="textarea"]:focus-within {{
        border-color: {acc} !important;
        box-shadow: 0 0 0 3px {acc_soft};
    }}
    [data-baseweb="input"]:has(input:disabled) {{
        background: {C['gray-5']} !important;
        border-color: {C['border-light']} !important;
    }}
    [data-baseweb="input"] input, [data-baseweb="textarea"] textarea {{
        font-family: {FONT_FAMILY};
        font-size: {FONT_SIZE};
        color: {C['text-primary']};
    }}
    [data-baseweb="input"] input::placeholder,
    [data-baseweb="textarea"] textarea::placeholder {{
        color: {C['text-muted']};
    }}
    [data-testid="stWidgetLabel"] p {{
        font-family: {FONT_FAMILY};
        font-size: 12px;
        font-weight: 600;
        color: {C['text-secondary']};
    }}
    """

    return {"select": select, "radio": radio, "expander": expander, "inputs": inputs}


# ==========================================================
# PUBLIC API
# ==========================================================

def apply_widget_styles(*parts: str) -> None:
    """Inject one <style> block. No arguments = all parts."""
    css = _css_parts()
    names: Sequence[str] = parts or tuple(css)

    unknown = [n for n in names if n not in css]
    if unknown:
        raise ValueError(f"Unknown style part(s): {unknown}. Choose from {list(css)}")

    st.html("<style>" + "".join(css[n] for n in names) + "</style>")


# Backward-compatible wrappers (same names as before)
def style_selectbox() -> None:
    apply_widget_styles("select")


def style_radio() -> None:
    apply_widget_styles("radio")


def apply_expander_style() -> None:
    apply_widget_styles("expander")


def style_inputs() -> None:
    apply_widget_styles("inputs")
