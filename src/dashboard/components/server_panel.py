"""
Server Compliance & Server Hosting Infrastructure Panels (Separated).

Features:
- Dedicated Server Compliance Panel: Role breakdown, online %, server fleet metrics.
- Dedicated Server Hosting Panel: Hosting types donut (AWS, Azure, GCP, Physical Hardware, VMs) — role matrix removed.
"""

from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import dcc, html

from src.dashboard import charts, theme as T


def build_server_compliance_panel(server_data: dict) -> dbc.Card:
    """
    Dedicated Server Compliance & Role Distribution Panel.
    """
    role_fig = charts.server_role_bar(server_data.get("role_counts", {}))
    total_servers = server_data.get("server_count", 0)
    online_pct = server_data.get("server_online_pct", 100.0)

    return dbc.Card(
        [
            dbc.CardHeader(
                html.Span([
                    html.Span("🖧", style={"marginRight": "8px"}),
                    html.Span("Server Fleet Compliance & Roles", style=T.FONT_SECTION_TITLE),
                    dbc.Badge(f"{total_servers} Servers", color="primary", className="ms-2"),
                    dbc.Badge(f"{online_pct:.1f}% Online", color="success" if online_pct >= 85 else "warning", className="ms-1"),
                ]),
                style={"backgroundColor": T.BG_CARD, "borderBottom": f"1px solid {T.BORDER}"},
            ),
            dbc.CardBody(
                [
                    dcc.Graph(figure=role_fig, config={"displayModeBar": False}, style={"height": "270px"}),
                ],
                style={"padding": "12px"},
            ),
        ],
        style={"backgroundColor": T.BG_CARD, "border": f"1px solid {T.BORDER}", "borderRadius": "8px", "height": "100%"},
    )


def build_server_hosting_panel(server_data: dict) -> dbc.Card:
    """
    Dedicated Server Hosting & Cloud Infrastructure Panel.
    Displays AWS, Azure, GCP, Physical Hardware, and Virtual Machines (VMs).
    Role matrix table removed as requested.
    """
    hosting_counts = server_data.get("hosting_counts", {})
    hosting_fig = charts.hosting_donut(hosting_counts)
    total_hosted = sum(hosting_counts.values())

    # Build summary badges
    badges = []
    for h_type, count in hosting_counts.items():
        if count > 0:
            color = T.HOSTING_COLORS.get(h_type, T.TEXT_SECONDARY)
            badges.append(
                html.Span(
                    [
                        html.Span(f"● {h_type}: ", style={"color": color, "fontWeight": "600"}),
                        html.Span(f"{count} ({count/total_hosted*100:.1f}%)" if total_hosted > 0 else "0", style={"color": T.TEXT_PRIMARY}),
                    ],
                    style={"marginRight": "18px", "fontSize": "0.82rem"},
                )
            )

    return dbc.Card(
        [
            dbc.CardHeader(
                dbc.Row(
                    [
                        dbc.Col(
                            html.Span([
                                html.Span("☁️", style={"marginRight": "8px"}),
                                html.Span("Server Hosting Infrastructure (Cloud & Virtualization)", style=T.FONT_SECTION_TITLE),
                                dbc.Badge(f"{total_hosted} Total Servers", color="secondary", className="ms-2"),
                            ]),
                            md=6,
                        ),
                        dbc.Col(
                            html.Div(
                                badges,
                                style={"display": "flex", "flexWrap": "wrap", "justifyContent": "flex-end", "alignItems": "center"},
                            ),
                            md=6,
                        ),
                    ],
                    align="center",
                ),
                style={"backgroundColor": T.BG_CARD, "borderBottom": f"1px solid {T.BORDER}"},
            ),
            dbc.CardBody(
                [
                    dcc.Graph(figure=hosting_fig, config={"displayModeBar": False}, style={"height": "280px"}),
                ],
                style={"padding": "10px"},
            ),
        ],
        style={"backgroundColor": T.BG_CARD, "border": f"1px solid {T.BORDER}", "borderRadius": "8px", "marginBottom": "20px"},
    )
