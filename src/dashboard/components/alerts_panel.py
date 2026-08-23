"""Alerts & incidents panel."""

from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import dcc, html

from src.dashboard import charts, theme as T


def build_alerts_panel(alert_data: dict) -> dbc.Card:
    severity_fig = charts.alert_severity_pie(alert_data.get("severity_counts", {}))
    sparkline_fig = charts.alert_trend_sparkline(alert_data.get("trend_7d", []))
    recent_critical = alert_data.get("recent_critical", [])

    critical_rows = [
        html.Tr([
            html.Td("🚨", style={"width": "28px"}),
            html.Td(a.get("device", "Unknown"), style={"color": T.TEXT_PRIMARY, "fontSize": "0.82rem"}),
            html.Td(a.get("message", "—"), style={"color": T.TEXT_SECONDARY, "fontSize": "0.78rem",
                                                    "maxWidth": "200px", "overflow": "hidden",
                                                    "textOverflow": "ellipsis", "whiteSpace": "nowrap"}),
        ])
        for a in recent_critical[:6]
    ] or [html.Tr([html.Td("✅ No critical alerts", colSpan=3,
                            style={"color": T.RAG_GREEN, "fontSize": "0.82rem"})])]

    total = alert_data.get("total_alerts", 0)
    critical_count = alert_data.get("critical_count", 0)
    badge_color = "danger" if critical_count > 0 else "success"

    return dbc.Card(
        [
            dbc.CardHeader(
                html.Span([
                    html.Span("🚨", style={"marginRight": "8px"}),
                    html.Span("Active Alerts", style=T.FONT_SECTION_TITLE),
                    dbc.Badge(f"{total} total", color="secondary", className="ms-2"),
                    dbc.Badge(f"{critical_count} critical", color=badge_color, className="ms-1"),
                ]),
                style={"backgroundColor": T.BG_CARD, "borderBottom": f"1px solid {T.BORDER}"},
            ),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col(dcc.Graph(figure=severity_fig, config={"displayModeBar": False},
                                      style={"height": "220px"}), md=5),
                    dbc.Col([
                        html.Div("7-Day Alert Trend", style={**T.FONT_KPI_LABEL, "marginBottom": "4px"}),
                        dcc.Graph(figure=sparkline_fig, config={"displayModeBar": False},
                                  style={"height": "140px"}),
                    ], md=7),
                ], className="mb-3"),

                html.Hr(style={"borderColor": T.BORDER}),
                html.Span("Recent Critical Alerts", style={**T.FONT_SECTION_TITLE,
                                                            "color": T.ACCENT_RED,
                                                            "display": "block", "marginBottom": "8px"}),
                dbc.Table(
                    [html.Tbody(critical_rows)],
                    bordered=False, hover=True, size="sm",
                ),
            ]),
        ],
        style={"backgroundColor": T.BG_CARD, "border": f"1px solid {T.BORDER}", "borderRadius": "8px"},
    )
