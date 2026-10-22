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
    """Single KPI card with icon, value, label, and optional subtitle."""
    p = T.get_theme_palette(theme_mode)
    return dbc.Card(
        dbc.CardBody(
            [
                html.Div(
                    [
                        html.Span(icon, style={"fontSize": "1.3rem", "marginRight": "8px"}),
                        html.Span(label, style={**T.FONT_KPI_LABEL, "color": p["text_secondary"]}),
                    ],
                    style={"display": "flex", "alignItems": "center", "marginBottom": "6px"},
                ),
                html.Div(
                    value,
                    style={**T.FONT_KPI_VALUE, "color": color},
                ),
                html.Div(
                    subtitle,
                    style={**T.FONT_BODY, "marginTop": "4px", "fontSize": "0.78rem", "color": p["text_secondary"]},
                ) if subtitle else html.Div(),
            ],
            style={"padding": "14px 16px"},
        ),
        style={
            "backgroundColor": p["bg_card"],
            "border": f"1px solid {p['border']}",
            "borderLeft": f"4px solid {color}",
            "borderRadius": "8px",
            "height": "100%",
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
