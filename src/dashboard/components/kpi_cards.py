"""
KPI Metric Card components — top-row executive summary strip.

Cleaned up: Alerts card removed and replaced with EOL at Risk & Total Servers.
"""

from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import html

from src.dashboard import theme as T


def _rag_color(rag: str) -> str:
    return {"GREEN": T.RAG_GREEN, "AMBER": T.RAG_AMBER, "RED": T.RAG_RED}.get(rag, T.TEXT_SECONDARY)


def kpi_card(
    value: str,
    label: str,
    icon: str,
    color: str = T.ACCENT_BLUE,
    subtitle: str = "",
    theme_mode: str = "dark",
) -> dbc.Card:
    """Compact dynamic Liquid Glass KPI card with large numbers display and concise metrics."""
    p = T.get_theme_palette(theme_mode)
    is_dark = p.get("is_dark", True)
    badge_bg = "rgba(255, 255, 255, 0.06)" if is_dark else "rgba(15, 23, 42, 0.04)"
    badge_border = "rgba(255, 255, 255, 0.1)" if is_dark else "rgba(203, 213, 225, 0.8)"

    return dbc.Card(
        dbc.CardBody(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.Span(icon, style={"fontSize": "1.05rem", "marginRight": "6px"}),
                                html.Span(
                                    label,
                                    style={
                                        **T.FONT_KPI_LABEL,
                                        "color": p["text_secondary"],
                                        "fontSize": "0.72rem",
                                        "letterSpacing": "0.06em",
                                    },
                                ),
                            ],
                            className="glass-pill-badge",
                            style={
                                "display": "inline-flex",
                                "alignItems": "center",
                                "padding": "2px 8px",
                                "borderRadius": "20px",
                                "backgroundColor": badge_bg,
                                "border": f"1px solid {badge_border}",
                            },
                        ),
                    ],
                    style={"display": "flex", "alignItems": "center", "justifyContent": "center", "marginBottom": "4px"},
                ),
                html.Div(
                    value,
                    className="kpi-large-number",
                    style={
                        **T.FONT_KPI_VALUE,
                        "color": color,
                        "textAlign": "center",
                    },
                ),
                html.Div(
                    subtitle,
                    style={
                        "marginTop": "4px",
                        "fontSize": "0.76rem",
                        "fontWeight": "500",
                        "color": p["text_secondary"],
                        "textAlign": "center",
                        "whiteSpace": "nowrap",
                        "overflow": "hidden",
                        "textOverflow": "ellipsis",
                    },
                ) if subtitle else html.Div(),
            ],
            style={"padding": "12px 14px"},
        ),
        className="liquid-glass-kpi",
        style={
            "position": "relative",
            "borderRadius": "14px",
            "border": f"1px solid {p['border']}",
            "borderLeft": f"4px solid {color}",
            "height": "100%",
            "overflow": "hidden",
            "backdropFilter": "blur(16px) saturate(180%)",
            "WebkitBackdropFilter": "blur(16px) saturate(180%)",
        },
    )


def build_kpi_strip(data, theme_mode: str = "dark") -> dbc.Row:
    """
    Build the top-row KPI strip from DashboardData.

    Cards in order:
      1. Total Servers
      2. Devices Online
      3. Devices Offline
      4. Patch Coverage
      5. EOL Devices
    """
    eol_count = data.eol_risk_count
    total_devs = data.total_devices
    online_devs = data.online_devices
    offline_devs = max(0, total_devs - online_devs)
    offline_pct = (offline_devs / total_devs * 100) if total_devs > 0 else 0.0

    patch_cov = float(data.patches.get("patch_coverage_pct", 0.0))
    patch_cov_color = T.RAG_GREEN if patch_cov >= 80 else T.RAG_AMBER if patch_cov >= 60 else T.RAG_RED

    server_count = data.servers.get("server_count", 0)
    server_online_pct = data.servers.get("server_online_pct", 0)

    cards = [
        # 1. Total Servers
        dbc.Col(
            kpi_card(
                value=str(server_count),
                label="Total Servers",
                icon="🖧",
                color=T.ACCENT_PURPLE,
                subtitle=f"{server_online_pct:.1f}% servers online",
                theme_mode=theme_mode,
            ),
            xs=12, sm=6, md=4, lg=True,
        ),
        # 2. Devices Online
        dbc.Col(
            kpi_card(
                value=str(online_devs),
                label="Devices Online",
                icon="🟢",
                color=T.ACCENT_TEAL,
                subtitle=f"{data.online_pct:.1f}% online ({online_devs}/{total_devs})",
                theme_mode=theme_mode,
            ),
            xs=12, sm=6, md=4, lg=True,
        ),
        # 3. Devices Offline
        dbc.Col(
            kpi_card(
                value=str(offline_devs),
                label="Devices Offline",
                icon="🔴",
                color=T.ACCENT_RED if offline_devs > 0 else T.RAG_GREEN,
                subtitle=f"{offline_pct:.1f}% offline",
                theme_mode=theme_mode,
            ),
            xs=12, sm=6, md=4, lg=True,
        ),
        # 4. Patch Coverage
        dbc.Col(
            kpi_card(
                value=f"{patch_cov:.1f}%",
                label="Patch Coverage",
                icon="🛡️",
                color=patch_cov_color,
                subtitle=f"{data.patches.get('installed_patches', 0):,} installed",
                theme_mode=theme_mode,
            ),
            xs=12, sm=6, md=4, lg=True,
        ),
        # 5. EOL Devices
        dbc.Col(
            kpi_card(
                value=str(eol_count),
                label="EOL Devices",
                icon="⚠️",
                color=T.ACCENT_RED if eol_count > 0 else T.RAG_GREEN,
                subtitle=f"OS Compliance: {data.os.get('os_compliance_pct', 0):.1f}%",
                theme_mode=theme_mode,
            ),
            xs=12, sm=6, md=4, lg=True,
        ),
    ]

    return dbc.Row(cards, className="g-3 mb-3")
