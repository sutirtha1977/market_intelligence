# app.py

import streamlit as st
from streamlit_option_menu import option_menu
from zoneinfo import ZoneInfo
from html import escape
from datetime import datetime

from core.styles import (
    CARD_SHADOW,
    CARD_SHADOW_HOVER,
    COLOR_MAP,
    FONT_FAMILY,
)


# ============================================================================
# THEME HELPERS
# ============================================================================

def color(key, fallback):
    """Safely retrieve a color from core.styles.COLOR_MAP."""
    return COLOR_MAP.get(key, fallback)


THEME = {
    "background": "#F5F7FB",
    "surface": color("gray-0", "#FFFFFF"),
    "sidebar_bg": color("gray-0", "#FFFFFF"),
    "primary": color("blue-60", "#2563EB"),
    "primary_dark": color("blue-80", "#1E3A8A"),
    "primary_light": color("primary-light", "#DBEAFE"),
    "text": color("text-primary", "#0F172A"),
    "text_secondary": color("text-secondary", "#475569"),
    "text_muted": color("text-muted", "#94A3B8"),
    "border": color("border-light", "#E2E8F0"),
    "card_shadow": CARD_SHADOW,
    "card_shadow_hover": CARD_SHADOW_HOVER,
}

# Each section gets its own accent: (main, dark, soft tint, gradient end)
SECTION_ACCENTS = {
    "home":                   ("#4F46E5", "#312E81", "#E0E7FF", "#818CF8"),
    "global_overview":        ("#0891B2", "#164E63", "#CFFAFE", "#22D3EE"),
    "usa_equity":             ("#E11D48", "#9F1239", "#FFE4E6", "#FB7185"),
    "india_equity":           (color("blue-60", "#2563EB"),   color("blue-80", "#1E3A8A"),     "#DBEAFE", "#38BDF8"),
    "nse_index_overview":     (color("teal-50", "#0D9488"),   color("teal-90", "#134E4A"),     "#CCFBF1", "#22D3EE"),
    "derivative_dashboard":   (color("orange-70", "#EA580C"), color("orange-90", "#9A3412"),   "#FFEDD5", "#FB923C"),
    "scanner_operations":     (color("green-70", "#16A34A"),  color("green-90", "#14532D"),    "#DCFCE7", "#10B981"),
    "backtesting_operations": (color("yellow-70", "#D97706"), color("yellow-90", "#92400E"),   "#FEF3C7", "#FACC15"),
    "playground":             (color("violet-70", "#7C3AED"), color("violet-90", "#4C1D95"),   "#EDE9FE", "#6366F1"),
    "admin_operations":       (color("gray-70", "#475569"),   color("gray-90", "#0F172A"),     "#E2E8F0", "#94A3B8"),
}


def get_accent(menu):
    return SECTION_ACCENTS.get(menu, SECTION_ACCENTS["india_equity"])


# ============================================================================
# GLOBAL CSS
# ============================================================================

def get_app_css():

    return f"""
    <style>
    @import url(
        "https://cdnjs.cloudflare.com/ajax/libs/bootstrap-icons/1.11.3/font/bootstrap-icons.min.css"
    );

    html, body, [data-testid="stAppViewContainer"] {{
        font-family: {FONT_FAMILY};
        background: {THEME["background"]};
    }}

    [data-testid="stAppViewContainer"] {{
        background:
            radial-gradient(900px 300px at 85% -80px, var(--accent-soft, #DBEAFE) 0%, transparent 70%),
            {THEME["background"]};
    }}

    /* Slim brand strip across the top of the page */
    [data-testid="stAppViewContainer"]::before {{
        content: "";
        position: fixed;
        inset: 0 0 auto 0;
        height: 4px;
        z-index: 1000;
        background: linear-gradient(90deg, #2563EB 0%, #0D9488 40%, #7C3AED 75%, #F97316 100%);
    }}

    [data-testid="stHeader"] {{
        background: transparent;
    }}

    [data-testid="stMain"] {{
        background: transparent;
    }}

    [data-testid="stMainBlockContainer"] {{
        max-width: 1440px;
        padding: 2.5rem 2rem 3rem;
    }}

    /* ---------- Sidebar ---------- */

    section[data-testid="stSidebar"] {{
        background: {THEME["sidebar_bg"]};
        border-right: 1px solid {THEME["border"]};
    }}

    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {{
        color: {THEME["text_secondary"]};
    }}

    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {{
        color: {THEME["text_muted"]};
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.1em;
    }}

    [data-testid="stSidebar"] hr {{
        border-color: {THEME["border"]};
    }}

    .sidebar-card {{
        display: flex;
        align-items: center;
        gap: 0.8rem;
        padding: 0.9rem 1rem;
        margin: 0.5rem 0 1.25rem;
        border: 1px solid {THEME["border"]};
        border-radius: 14px;
        background: linear-gradient(135deg, #FFFFFF 0%, var(--accent-soft, #DBEAFE) 160%);
        box-shadow: {THEME["card_shadow"]};
    }}

    .sidebar-mark {{
        display: grid;
        flex: 0 0 2.6rem;
        width: 2.6rem;
        height: 2.6rem;
        place-items: center;
        border-radius: 12px;
        color: #FFFFFF;
        background: linear-gradient(135deg, var(--accent, #2563EB), var(--accent-end, #38BDF8));
        box-shadow: 0 6px 14px var(--accent-shadow, rgba(37, 99, 235, 0.3));
        font-size: 1.15rem;
    }}

    .sidebar-title {{
        color: {THEME["text"]};
        font-size: 1.05rem;
        font-weight: 800;
        letter-spacing: 0.02em;
        line-height: 1.2;
    }}

    .sidebar-tagline {{
        margin-top: 0.15rem;
        color: {THEME["text_secondary"]};
        font-size: 0.72rem;
    }}

    /* ---------- Section header ---------- */

    .section-card {{
        position: relative;
        display: flex;
        align-items: center;
        gap: 1.1rem;
        overflow: hidden;
        padding: 1.2rem 1.4rem;
        border: 1px solid {THEME["border"]};
        border-radius: 16px;
        background:
            linear-gradient(100deg, var(--accent-soft, #DBEAFE) 0%, #FFFFFF 55%),
            {THEME["surface"]};
        box-shadow: {THEME["card_shadow"]};
        transition: box-shadow 160ms ease;
    }}

    .section-card::before {{
        content: "";
        position: absolute;
        inset: 0 auto 0 0;
        width: 5px;
        background: linear-gradient(180deg, var(--accent, #2563EB), var(--accent-end, #38BDF8));
    }}

    .section-card:hover {{
        box-shadow: {THEME["card_shadow_hover"]};
    }}

    .section-icon {{
        display: grid;
        flex: 0 0 3rem;
        width: 3rem;
        height: 3rem;
        place-items: center;
        border-radius: 14px;
        background: #FFFFFF;
        border: 1px solid var(--accent-soft, #DBEAFE);
        box-shadow: 0 4px 12px var(--accent-shadow, rgba(37, 99, 235, 0.18));
        font-size: 1.35rem;
    }}

    .section-icon i {{
        color: var(--accent, #2563EB);
        line-height: 1;
    }}

    .section-text {{
        flex: 1 1 auto;
        min-width: 0;
    }}

    .section-title {{
        margin: 0;
        padding: 0;
        color: var(--accent-dark, {THEME["text"]});
        font-size: 1.4rem;
        font-weight: 750;
        line-height: 1.25;
    }}

    .section-subtitle {{
        margin: 0.25rem 0 0;
        color: {THEME["text_secondary"]};
        font-size: 0.87rem;
    }}

    .section-chip {{
        display: inline-flex;
        flex: 0 0 auto;
        align-items: center;
        gap: 0.45rem;
        padding: 0.35rem 0.8rem;
        border: 1px solid {THEME["border"]};
        border-radius: 999px;
        color: {THEME["text_secondary"]};
        background: #FFFFFF;
        font-size: 0.76rem;
        font-weight: 600;
        white-space: nowrap;
    }}

    .section-chip .dot {{
        width: 0.5rem;
        height: 0.5rem;
        border-radius: 50%;
        background: {color("green-50", "#22C55E")};
        box-shadow: 0 0 0 3px {color("green-30", "#DCFCE7")};
    }}

    .section-divider {{
        height: 1px;
        margin: 1.1rem 0 1.5rem;
        background: linear-gradient(90deg, var(--accent, #2563EB) 0%, {THEME["border"]} 30%, transparent 100%);
        opacity: 0.8;
    }}

    /* ---------- Streamlit components (for the pages you build next) ---------- */

    .stButton > button, .stDownloadButton > button {{
        border: 0;
        border-radius: 10px;
        color: #FFFFFF;
        background: linear-gradient(135deg, var(--accent, #2563EB), var(--accent-end, #38BDF8));
        box-shadow: 0 4px 12px var(--accent-shadow, rgba(37, 99, 235, 0.25));
        font-weight: 600;
        transition: transform 120ms ease, box-shadow 120ms ease, filter 120ms ease;
    }}

    .stButton > button:hover, .stDownloadButton > button:hover {{
        color: #FFFFFF;
        filter: brightness(1.06);
        transform: translateY(-1px);
        box-shadow: 0 8px 18px var(--accent-shadow, rgba(37, 99, 235, 0.3));
    }}

    .stButton > button:focus-visible {{
        outline: 3px solid var(--accent-soft, #DBEAFE);
        outline-offset: 2px;
    }}

    [data-testid="stMetric"] {{
        padding: 1rem 1.1rem;
        border: 1px solid {THEME["border"]};
        border-top: 3px solid var(--accent, #2563EB);
        border-radius: 14px;
        background: {THEME["surface"]};
        box-shadow: {THEME["card_shadow"]};
    }}

    [data-testid="stMetricLabel"] {{
        color: {THEME["text_secondary"]};
        font-weight: 600;
    }}

    [data-testid="stMetricValue"] {{
        color: {THEME["text"]};
        font-weight: 750;
    }}

    .stTabs [data-baseweb="tab-list"] {{
        gap: 0.25rem;
        border-bottom: 1px solid {THEME["border"]};
    }}

    .stTabs [data-baseweb="tab"] {{
        color: {THEME["text_secondary"]};
        font-weight: 600;
    }}

    .stTabs [aria-selected="true"] {{
        color: var(--accent-dark, #1E3A8A);
    }}

    .stTabs [data-baseweb="tab-highlight"] {{
        background: var(--accent, #2563EB);
        height: 3px;
    }}

    [data-testid="stDataFrame"], [data-testid="stTable"] {{
        overflow: hidden;
        border: 1px solid {THEME["border"]};
        border-radius: 12px;
        box-shadow: {THEME["card_shadow"]};
    }}

    [data-baseweb="input"]:focus-within, [data-baseweb="select"]:focus-within {{
        border-color: var(--accent, #2563EB);
        box-shadow: 0 0 0 3px var(--accent-soft, #DBEAFE);
    }}

    /* ---------- Footer ---------- */

    .footer-card {{
        margin-top: 3rem;
        padding: 0.9rem;
        border: 1px solid {THEME["border"]};
        border-radius: 12px;
        color: {THEME["text_muted"]};
        background: {THEME["surface"]};
        text-align: center;
        font-size: 0.75rem;
    }}

    @media (max-width: 640px) {{
        [data-testid="stMainBlockContainer"] {{
            padding: 1.5rem 1rem 2rem;
        }}

        .section-card {{
            padding: 0.9rem 1rem;
        }}

        .section-title {{
            font-size: 1.15rem;
        }}

        .section-chip {{
            display: none;
        }}
    }}

    @media (prefers-reduced-motion: reduce) {{
        * {{
            transition: none !important;
        }}
    }}
    </style>
    """


def get_accent_css(menu):
    """CSS variables that recolor the page for the active section."""

    main, dark, soft, end = get_accent(menu)
    shadow = main.lstrip("#")
    r, g, b = (int(shadow[i:i + 2], 16) for i in (0, 2, 4))

    return f"""
    <style>
    :root {{
        --accent: {main};
        --accent-dark: {dark};
        --accent-soft: {soft};
        --accent-end: {end};
        --accent-shadow: rgba({r}, {g}, {b}, 0.28);
    }}
    </style>
    """


# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

def setup_page():

    st.set_page_config(
        page_title="Analytics Platform",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.html(get_app_css())


# ============================================================================
# SESSION STATE
# ============================================================================

def initialize_session_state():

    defaults = {
        "current_menu": "home",
        "current_operation": None,
    }

    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def handle_menu_change(selected_menu):

    if selected_menu and st.session_state.current_menu != selected_menu:

        st.session_state.current_menu = selected_menu
        st.session_state.current_operation = None

        # Rerun so the accent color and sidebar highlight match the new section
        st.rerun()


# ============================================================================
# SECTION HEADER
# ============================================================================

def _icon_html(icon):
    """Bootstrap icon name (e.g. 'graph-up-arrow') or an emoji."""
    icon = str(icon)
    if icon.isascii() and icon.replace("-", "").isalnum():
        return f'<i class="bi bi-{escape(icon)}"></i>'
    return escape(icon)


def render_section_header(
    title,
    subtitle=None,
    icon="graph-up-arrow"
):

    safe_title = escape(str(title))
    safe_subtitle = escape(str(subtitle)) if subtitle else ""
    safe_icon = _icon_html(icon)
    # today = datetime.now().strftime("%d %b %Y")
    now = datetime.now().astimezone()
    ist_now = now.astimezone(ZoneInfo("Asia/Kolkata"))

    today = (
        f"{now.strftime('%A, %d %b %Y %Z')} "
        f"| IST: {ist_now.strftime('%A, %d %b %Y %I:%M %p IST')}"
    )

    st.html(f"""
        <div class="section-card">
            <div class="section-icon">{safe_icon}</div>
            <div class="section-text">
                <h2 class="section-title">{safe_title}</h2>
                <p class="section-subtitle">{safe_subtitle}</p>
            </div>
            <div class="section-chip"><span class="dot"></span>{today}</div>
        </div>
    """)
    st.html('<div class="section-divider"></div>')


# ============================================================================
# SIDEBAR HEADER
# ============================================================================

def render_sidebar_header():

    st.html("""
        <div class="sidebar-card">
            <div class="sidebar-mark"><i class="bi bi-graph-up-arrow"></i></div>
            <div>
                <div class="sidebar-title">Analytics</div>
                <div class="sidebar-tagline">Markets · Signals · Insights</div>
            </div>
        </div>
    """)


# ============================================================================
# SIDEBAR NAVIGATION
# ============================================================================

def render_sidebar_menu():

    menu_options = [
        "Home",
        # "Global Trends",
        # "INDIA Equity",
        # "USA Equity",
        # "NSE Indices",
        # "Equity Signals",
        "Scanners",
        # "Strategy Builder",
        "System Admin",
    ]

    icons = [
        "house-fill",
        # "globe",
        # "bar-chart-fill",
        # "currency-dollar",
        # "graph-up-arrow",
        # "clock-history",
        "search-heart-fill",
        # "cpu-fill",
        "gear-fill",
    ]

    menu_map = {
        "Home": "home",
        # "Global Trends": "global_overview",
        # "INDIA Equity": "india_equity",
        # "USA Equity": "usa_equity",
        # "NSE Indices": "nse_index_overview",
        # "Equity Signals": "scanner_operations",
        "Scanners": "scanner_operations",
        # "Strategy Builder": "playground",
        "System Admin": "admin_operations",
    }

    current_menu = st.session_state.current_menu
    accent, accent_dark, accent_soft, accent_end = get_accent(current_menu)

    reverse_menu_map = {
        value: key for key, value in menu_map.items()
    }

    default_option = reverse_menu_map.get(
        current_menu,
        "Home"
    )

    default_index = menu_options.index(default_option)

    with st.sidebar:

        render_sidebar_header()

        st.caption("NAVIGATION")

        menu_choice = option_menu(
            menu_title=None,
            options=menu_options,
            icons=icons,
            default_index=default_index,
            orientation="vertical",
            key="main_navigation",

            styles={

                "container": {
                    "padding": "0.4rem 0.2rem",
                    "background-color": "transparent",
                },

                "icon": {
                    "font-size": "17px",
                    "color": "inherit",
                },

                "nav-link": {
                    "font-size": "14px",
                    "font-weight": "500",
                    "color": THEME["text_secondary"],
                    "text-align": "left",
                    "margin": "4px 0",
                    "padding": "11px 14px",
                    "border-radius": "10px",
                    "background-color": "transparent",
                    "transition": "all 0.2s ease",
                },

                "nav-link-hover": {
                    "background-color": accent_soft,
                    "color": accent_dark,
                },

                "nav-link-selected": {
                    "background": f"linear-gradient(135deg, {accent}, {accent_end})",
                    "color": "#FFFFFF",
                    "font-weight": "600",
                    "box-shadow": f"0 6px 14px {accent}40",
                },
            }
        )

    return menu_map.get(menu_choice, "home")


# ============================================================================
# CONTENT ROUTING
# ============================================================================

def render_content_box(menu):

    if menu == "home":
        render_section_header(
            "MARKET OVERVIEW",
            "Real-time market insights and performance analytics",
            "graph-up-arrow"
        )
        from operations.home_dashboard.home_view import handle_home_operations
        handle_home_operations()

    # elif menu == "global_overview":
    #     render_section_header(
    #         "GLOBAL TRENDS",
    #         "International market trends and correlations",
    #         "globe"
    #     )
    #     from operations.global_dashboard.global_overview_ops import handle_dashboard_ops
    #     handle_dashboard_ops()

    # elif menu == "india_equity":
    #     render_section_header(
    #         "INDIA EQUITY",
    #         "Indian stock market analysis and portfolio tracking",
    #         "bar-chart-fill"
    #     )
    #     from operations.main_dashboard.equity_view import equity_view
    #     equity_view(asset_key="yahoo_india_equity", region_prefix="india")

    # elif menu == "usa_equity":
    #     render_section_header(
    #         "USA EQUITY",
    #         "US stock market analysis and portfolio tracking",
    #         "currency-dollar"
    #     )
    #     from operations.main_dashboard.equity_view import equity_view
    #     equity_view(asset_key="yahoo_usa_equity", region_prefix="usa")

    # elif menu == "nse_index_overview":
    #     render_section_header(
    #         "INDEX TRACKING",
    #         "India's national stock exchange indices",
    #         "graph-up-arrow"
    #     )
    #     from operations.nse_dashboard.nse_dashboard_engine import handle_index_overview_operations
    #     handle_index_overview_operations()

    # elif menu == "scanner_operations":
    #     render_section_header(
    #         "TRADE SIGNALS",
    #         "Automated trading signal detection",
    #         "clock-history"
    #     )
    #     from operations.scanners.scanner_ops import handle_scanner_operations
    #     handle_scanner_operations()

    elif menu == "scanner_operations":
        render_section_header(
            "TRADE SIGNALS",
            "Automated trading signal detection",
            "search"
        )
        from operations.ops_scanners.scanner_ops import handle_scanner_backtest_operations
        handle_scanner_backtest_operations()

    # elif menu == "playground":
    #     render_section_header(
    #         "STRATEGY BUILDER",
    #         "Experiment with custom strategies",
    #         "cpu"
    #     )
    #     from operations.playground_ops import handle_playground_operations
    #     handle_playground_operations()

    elif menu == "admin_operations":
        render_section_header(
            "SYSTEM SETTINGS",
            "Configuration and system management",
            "gear-fill"
        )
        from operations.ops_admin.admin_ops import handle_admin_operations
        handle_admin_operations()

    else:
        st.warning(f"Unknown application section: {escape(str(menu))}")


# ============================================================================
# FOOTER
# ============================================================================

def render_footer():

    year = datetime.now().year

    st.html(f"""
        <div class="footer-card">
            © {year} Analytics Platform
            <br>
            <span style="font-size:10px;">
                Market Intelligence • Trading Analytics • Strategy Research
            </span>
        </div>
    """)


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():

    setup_page()

    initialize_session_state()

    selected_menu = render_sidebar_menu()

    handle_menu_change(selected_menu)

    # Accent variables for the active section (must come after menu handling)
    st.html(get_accent_css(st.session_state.current_menu))

    render_content_box(
        st.session_state.current_menu
    )

    render_footer()


# ============================================================================
# APPLICATION ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()