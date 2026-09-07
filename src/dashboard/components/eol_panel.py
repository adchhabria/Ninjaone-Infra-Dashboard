"""
Dedicated End-of-Life (EOL) Compliance & Audit Panel.

Features:
- EOL Status Distribution Donut (Supported vs Approaching vs Expired)
- At-Risk OS Version Breakdown Bar Chart
- Full Interactive EOL Audit DataTable with Excel-style column filters, Days Overdue and Risk Ratings
"""

from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import dcc, html

from src.dashboard import charts, theme as T


def build_eol_panel(os_data: dict) -> dbc.Card:
    """
    Renders dedicated EOL graphs and status distribution badges.
    """
    status_counts = os_data.get("eol_status_counts", {})
    eol_by_os = os_data.get("eol_by_os", {})

    status_fig = charts.eol_status_donut(status_counts)
    by_os_fig = charts.eol_by_os_bar(eol_by_os)

    eol_count = os_data.get("eol_count", 0)
    approaching_count = os_data.get("approaching_count", 0)
    badge_color = "danger" if eol_count > 0 else "warning" if approaching_count > 0 else "success"

    return dbc.Card(
        [
            dbc.CardHeader(
                dbc.Row(
                    [
                        dbc.Col(
                            html.Span([
                                html.Span("⚠️", style={"marginRight": "8px"}),
                                html.Span("Operating System End-of-Life (EOL) & Lifecycle Audit", style=T.FONT_SECTION_TITLE),
                                dbc.Badge(f"{eol_count} Expired (Non-Compliant)", color=badge_color, className="ms-2"),
                                dbc.Badge(f"{approaching_count} Approaching EOL (<180d)", color="warning", className="ms-1"),
                            ]),
                            md=7,
                        ),
                        dbc.Col(
                            html.Div(
                                [
                                    dbc.Badge(f"{status_counts.get('Supported', 0)} Supported", color="success", className="me-2"),
                                    dbc.Badge(f"{status_counts.get('Approaching EOL', 0)} Approaching", color="warning", className="me-2"),
                                    dbc.Badge(f"{status_counts.get('Expired (EOL)', 0)} Expired", color="danger"),
                                ],
                                style={"textAlign": "right"},
                            ),
                            md=5,
                        ),
                    ],
                    align="center",
                ),
                style={"backgroundColor": T.BG_CARD, "borderBottom": f"1px solid {T.BORDER}"},
            ),
            dbc.CardBody(
                [
                    # Top Row: 2 EOL Visuals
                    dbc.Row(
                        [
                            dbc.Col(dcc.Graph(figure=status_fig, config={"displayModeBar": False}, style={"height": "250px"}), md=5),
                            dbc.Col(dcc.Graph(figure=by_os_fig, config={"displayModeBar": False}, style={"height": "250px"}), md=7),
                        ],
                        className="g-3",
                    ),
                ],
                style={"padding": "12px"},
            ),
        ],
        style={"backgroundColor": T.BG_CARD, "border": f"1px solid {T.BORDER}", "borderRadius": "8px", "marginBottom": "20px"},
    )
