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
                    style={"display": "flex", "alignItems": "center", "marginBottom": "4px"},
                ),
                html.Div(
                    value,
                    className="kpi-large-number",
                    style={
                        **T.FONT_KPI_VALUE,
                        "color": color,
                    },
                ),
                html.Div(
                    subtitle,
                    style={
                        "marginTop": "4px",
                        "fontSize": "0.76rem",
                        "fontWeight": "500",
                        "color": p["text_secondary"],
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

    Cards:
      1. Total Managed Devices
      2. Online Devices
      3. Overall Compliance Score (RAG color)
      4. Server Count
      5. EOL Devices at Risk
    """
    rag_color = _rag_color(data.compliance_rag)
    eol_count = data.eol_risk_count

    cards = [
        dbc.Col(
            kpi_card(
                value=str(data.total_devices),
                label="Total Managed Devices",
                icon="🖥️",
                color=T.ACCENT_BLUE,
                subtitle=f"{data.servers.get('server_count', 0)} servers · "
                         f"{data.servers.get('workstation_count', 0)} workstations",
                theme_mode=theme_mode,
            ),
            xs=12, sm=6, md=4, lg=True,
        ),
        dbc.Col(
            kpi_card(
                value=f"{data.online_pct:.1f}%",
                label="Devices Online",
                icon="🟢",
                color=T.ACCENT_TEAL,
                subtitle=f"{data.online_devices} of {data.total_devices} reachable",
                theme_mode=theme_mode,
            ),
            xs=12, sm=6, md=4, lg=True,
        ),
        dbc.Col(
            kpi_card(
                value=f"{data.overall_compliance_score:.1f}%",
                label="Compliance Score",
                icon="🛡️",
                color=rag_color,
                subtitle=f"Status: {data.compliance_rag} (Target: ≥80%)",
                theme_mode=theme_mode,
            ),
            xs=12, sm=6, md=4, lg=True,
        ),
        dbc.Col(
            kpi_card(
                value=str(data.servers.get("server_count", 0)),
                label="Servers Managed",
                icon="🖧",
                color=T.ACCENT_PURPLE,
                subtitle=f"{data.servers.get('server_online_pct', 0):.1f}% servers online",
                theme_mode=theme_mode,
            ),
            xs=12, sm=6, md=4, lg=True,
        ),
        dbc.Col(
            kpi_card(
                value=str(eol_count),
                label="EOL Devices at Risk",
                icon="⚠️",
                color=T.ACCENT_RED if eol_count > 0 else T.RAG_GREEN,
                subtitle=f"OS Compliance: {data.os.get('os_compliance_pct', 0):.1f}%",
                theme_mode=theme_mode,
            ),
            xs=12, sm=6, md=4, lg=True,
        ),
    ]

    return dbc.Row(cards, className="g-3 mb-3")
