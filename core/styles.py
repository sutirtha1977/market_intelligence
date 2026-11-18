
# core/styles.py

# ==========================================================
# GLOBAL TYPOGRAPHY
# ==========================================================

FONT_FAMILY = (
    "-apple-system, BlinkMacSystemFont, "
    "'SF Pro Text', 'Helvetica Neue', Helvetica, Arial, sans-serif"
)

FONT_SIZE = "13px"

CARD_SHADOW = "0 6px 18px rgba(15, 23, 42, 0.08)"

CARD_SHADOW_HOVER = "0 10px 28px rgba(37, 99, 235, 0.14)"


# ==========================================================
# COLOR SYSTEM
# Modern Financial Analytics Theme
# ==========================================================

COLOR_MAP = {

    # ======================================================
    # CORE BLUE SCALE
    # Primary brand and navigation
    # ======================================================

    "blue-90": "#101B33",
    "blue-80": "#1E3A8A",
    "blue-70": "#1D4ED8",
    "blue-60": "#2563EB",
    "blue-50": "#3B82F6",
    "blue-30": "#BFDBFE",
    "blue-100": "#DBEAFE",
    "blue-500": "#3B82F6",
    "blue-600": "#2563EB",
    "blue-700": "#1D4ED8",

    # ======================================================
    # TEAL SCALE
    # Secondary brand and analytics
    # ======================================================

    "teal-90": "#134E4A",
    "teal-70": "#0F766E",
    "teal-50": "#0D9488",
    "teal-30": "#99F6E4",

    # ======================================================
    # VIOLET SCALE
    # AI and strategy modules
    # ======================================================

    "violet-90": "#4C1D95",
    "violet-70": "#7C3AED",
    "violet-50": "#8B5CF6",
    "violet-30": "#DDD6FE",
    "violet-500": "#8B5CF6",
    "violet-600": "#7C3AED",
    "violet-700": "#6D28D9",

    # ======================================================
    # GREEN SCALE
    # Bullish / positive
    # ======================================================

    "green-90": "#14532D",
    "green-70": "#16A34A",
    "green-50": "#22C55E",
    "green-40": "#86EFAC",
    "green-30": "#DCFCE7",

    "emerald-500": "#10B981",
    "emerald-600": "#059669",

    # ======================================================
    # RED SCALE
    # Bearish / negative
    # ======================================================

    "red-90": "#991B1B",
    "red-70": "#DC2626",
    "red-50": "#EF4444",
    "red-30": "#FECACA",

    "rose-500": "#F43F5E",
    "rose-600": "#E11D48",

    # ======================================================
    # ORANGE SCALE
    # ======================================================

    "orange-90": "#9A3412",
    "orange-70": "#EA580C",
    "orange-50": "#FB923C",
    "orange-30": "#FED7AA",

    # ======================================================
    # YELLOW SCALE
    # ======================================================

    "yellow-90": "#92400E",
    "yellow-70": "#D97706",
    "yellow-50": "#FACC15",
    "yellow-30": "#FEF3C7",

    # ======================================================
    # NEUTRAL SCALE
    # ======================================================

    "gray-90": "#0F172A",
    "gray-80": "#1E293B",
    "gray-70": "#475569",
    "gray-50": "#94A3B8",
    "gray-30": "#CBD5E1",
    "gray-20": "#E2E8F0",
    "gray-10": "#F1F5F9",
    "gray-5": "#F8FAFC",
    "gray-0": "#FFFFFF",

    # ======================================================
    # SEMANTIC COLORS
    # ======================================================

    "primary": "#2563EB",
    "primary-light": "#DBEAFE",

    "success": "#16A34A",
    "success-light": "#DCFCE7",

    "error": "#DC2626",
    "error-light": "#FEE2E2",

    "warning": "#D97706",
    "warning-light": "#FEF3C7",

    "info": "#2563EB",
    "info-light": "#DBEAFE",

    # ======================================================
    # FINANCIAL MARKET COLORS
    # ======================================================

    "bullish": "#16A34A",
    "bullish-bg": "#DCFCE7",

    "bearish": "#DC2626",
    "bearish-bg": "#FEE2E2",

    "neutral": "#64748B",
    "neutral-bg": "#F1F5F9",

    "ai-accent": "#7C3AED",
    "ai-accent-bg": "#EDE9FE",

    "signal-buy": "#16A34A",
    "signal-sell": "#DC2626",
    "signal-hold": "#D97706",

    # ======================================================
    # BACKGROUNDS
    # ======================================================

    "app-bg": "#F1F5F9",
    "bg-light": "#FFFFFF",
    "bg-surface": "#F8FAFC",
    "bg-card": "#FFFFFF",
    "card-bg": "#FFFFFF",

    # ======================================================
    # SIDEBAR
    # ======================================================

    "sidebar-bg": "#101B33",
    "sidebar-hover": "#1E3357",
    "sidebar-active": "#2563EB",

    # ======================================================
    # TEXT
    # ======================================================

    "text-primary": "#0F172A",
    "text-secondary": "#475569",
    "text-muted": "#94A3B8",
    "text-inverse": "#FFFFFF",

    "text-sidebar": "#CBD5E1",
    "text-sidebar-active": "#FFFFFF",

    # ======================================================
    # BORDERS
    # ======================================================

    "card-border": "#E2E8F0",

    "border-muted": "#CBD5E1",
    "border-light": "#E2E8F0",
    "border-subtle": "#CBD5E1",
    "border-dark": "#334155",

    # ======================================================
    # TABLES
    # ======================================================

    "table-row-alt": "#F8FAFC",
    "table-header": "#EAF1FB",
    "table-border": "#E2E8F0",

    # ======================================================
    # HOVER / INTERACTION
    # ======================================================

    "hover-blue": "#EFF6FF",
    "hover-bg": "#EFF6FF",

    # ======================================================
    # TABS
    # ======================================================

    "tab": "#2563EB",
    "tab-active": "#2563EB",
    "tab-inactive": "#64748B",

    # ======================================================
    # BASIC
    # ======================================================

    "black": "#000000",
    "white": "#FFFFFF",

    # ======================================================
    # GRADIENTS
    # ======================================================

    "primary-gradient": (
        "linear-gradient(135deg, #2563EB 0%, #0D9488 100%)"
    ),

    "secondary-gradient": (
        "linear-gradient(135deg, #0D9488 0%, #38BDF8 100%)"
    ),

    "accent-gradient": (
        "linear-gradient(135deg, #7C3AED 0%, #2563EB 100%)"
    ),

    "success-gradient": (
        "linear-gradient(135deg, #16A34A 0%, #0D9488 100%)"
    ),

    "warning-gradient": (
        "linear-gradient(135deg, #D97706 0%, #F59E0B 100%)"
    ),

    "danger-gradient": (
        "linear-gradient(135deg, #DC2626 0%, #F97316 100%)"
    ),
}

# ==========================================================
# END OF DESIGN SYSTEM
# ==========================================================
