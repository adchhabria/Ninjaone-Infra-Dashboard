"""
Professional dark theme constants for the NinjaOne Dashboard.

All charts and components import from here to ensure visual consistency.
"""

# ---------------------------------------------------------------------------
# Color Palette
# ---------------------------------------------------------------------------

BG_PRIMARY = "#0D1117"       # Page background
BG_CARD = "#161B22"          # Card / panel background
BG_CARD_HOVER = "#1C2128"    # Card hover state
BORDER = "#30363D"           # Subtle card border
TEXT_PRIMARY = "#E6EDF3"     # Main text
TEXT_SECONDARY = "#8B949E"   # Muted / label text
TEXT_MUTED = "#484F58"       # Very muted

# Accent Colors
ACCENT_BLUE = "#2F81F7"      # Primary brand
ACCENT_PURPLE = "#A371F7"    # Secondary / server
ACCENT_TEAL = "#39D353"      # Online / healthy green
ACCENT_ORANGE = "#F78166"    # Warning / amber
ACCENT_RED = "#FF7B72"       # Critical / danger
ACCENT_YELLOW = "#E3B341"    # Moderate / caution
ACCENT_CYAN = "#79C0FF"      # Info
ACCENT_PINK = "#F778BA"      # Highlight

# RAG Palette
RAG_GREEN = "#00C853"
RAG_AMBER = "#FFC107"
RAG_RED = "#F44336"

# ---------------------------------------------------------------------------
# OS Family Colors
# ---------------------------------------------------------------------------

OS_COLORS = {
    "Windows": ACCENT_BLUE,
    "Linux": ACCENT_TEAL,
    "macOS": ACCENT_PURPLE,
    "Other": TEXT_SECONDARY,
    "Unknown": TEXT_MUTED,
}

# ---------------------------------------------------------------------------
# Alert Severity Colors
# ---------------------------------------------------------------------------

SEVERITY_COLORS = {
    "CRITICAL": ACCENT_RED,
    "MAJOR": ACCENT_ORANGE,
    "MINOR": ACCENT_YELLOW,
    "WARNING": ACCENT_CYAN,
    "NONE": TEXT_SECONDARY,
}

# ---------------------------------------------------------------------------
# Hosting Colors
# ---------------------------------------------------------------------------

HOSTING_COLORS = {
    "Azure Server": "#0089D6",
    "Azure": "#0089D6",
    "AWS Server": "#FF9900",
    "AWS": "#FF9900",
    "VM Server": "#39C5BB",
    "Virtual Machines (VMs)": "#39C5BB",
    "Physical Server": "#8B949E",
    "Physical Hardware": "#8B949E",
    "On-Premise (Physical & VMs)": "#2F81F7",
    "Cloud (Azure & AWS)": "#0089D6",
    "GCP": "#4285F4",
    "N/A": TEXT_MUTED,
}

# ---------------------------------------------------------------------------
# Plotly Layout Template
# ---------------------------------------------------------------------------

PLOTLY_TEMPLATE = dict(
    layout=dict(
        paper_bgcolor=BG_CARD,
        plot_bgcolor=BG_CARD,
        font=dict(family="Inter, -apple-system, sans-serif", color=TEXT_PRIMARY, size=12),
        title=dict(font=dict(size=14, color=TEXT_PRIMARY), x=0.01, xanchor="left"),
        legend=dict(
            bgcolor=BG_CARD,
            bordercolor=BORDER,
            borderwidth=1,
            font=dict(color=TEXT_SECONDARY, size=11),
        ),
        margin=dict(l=12, r=12, t=36, b=12),
        xaxis=dict(
            gridcolor=BORDER,
            linecolor=BORDER,
            tickcolor=TEXT_SECONDARY,
            tickfont=dict(color=TEXT_SECONDARY),
        ),
        yaxis=dict(
            gridcolor=BORDER,
            linecolor=BORDER,
            tickcolor=TEXT_SECONDARY,
            tickfont=dict(color=TEXT_SECONDARY),
            zerolinecolor=BORDER,
        ),
        hoverlabel=dict(
            bgcolor=BG_CARD_HOVER,
            bordercolor=BORDER,
            font=dict(color=TEXT_PRIMARY),
        ),
    )
)

# ---------------------------------------------------------------------------
# Dash Bootstrap Theme
# ---------------------------------------------------------------------------

DBC_THEME_OVERRIDE = {
    "--bs-body-bg": BG_PRIMARY,
    "--bs-body-color": TEXT_PRIMARY,
    "--bs-card-bg": BG_CARD,
    "--bs-border-color": BORDER,
}

# ---------------------------------------------------------------------------
# Typography Scale
# ---------------------------------------------------------------------------

FONT_KPI_VALUE = {"fontSize": "2.4rem", "fontWeight": "700", "lineHeight": "1"}
FONT_KPI_LABEL = {"fontSize": "0.75rem", "fontWeight": "500", "letterSpacing": "0.08em",
                  "textTransform": "uppercase", "color": TEXT_SECONDARY}
FONT_SECTION_TITLE = {"fontSize": "0.9rem", "fontWeight": "600",
                       "textTransform": "uppercase", "letterSpacing": "0.06em"}
FONT_BODY = {"fontSize": "0.875rem", "color": TEXT_SECONDARY}
