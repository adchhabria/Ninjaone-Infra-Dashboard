"""
Hosting Infrastructure Panels — 2 Separate Boxes Side by Side.

Box 1: All Devices with 3 Radio Button Filters:
       1. All
       2. On-Premise (Physical & VMs)
       3. Cloud (Azure & AWS)
       Shows hosting donut breakdown and summary counters.

Box 2: Organization-wise Stacked Column Bar Graph Display.
"""

from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import dcc, html

from src.dashboard import charts, theme as T


def build_hosting_box_1(server_data: dict, filter_mode: str = "all") -> dbc.Card:
    """
    Box 1: Hosting breakdown donut with 3 radio button filters:
    1. All
    2. On-Premise (Physical & VMs)
    3. Cloud (Azure & AWS)
    """
    hosting_counts = server_data.get("hosting_counts", {})
    cloud_total = server_data.get("cloud_total", 0)
    onprem_total = server_data.get("onprem_total", 0)
    total_devices = server_data.get("total_devices", sum(hosting_counts.values()))

    cloud_pct = (cloud_total / total_devices * 100) if total_devices > 0 else 0.0
    onprem_pct = (onprem_total / total_devices * 100) if total_devices > 0 else 0.0

    hosting_fig = charts.hosting_donut(hosting_counts, filter_mode=filter_mode)

    return dbc.Card(
        [
            dbc.CardHeader(
                [
                    html.Div(
                        [
                            html.Span("☁️", style={"marginRight": "8px"}),
                            html.Span("Infrastructure Hosting Breakdown", style=T.FONT_SECTION_TITLE),
                            dbc.Badge(f"{total_devices:,} Total Devices", color="primary", className="ms-2"),
                        ],
                        className="d-flex align-items-center mb-2",
                    ),
                    # 3 Radio Button Filters
                    html.Div(
                        [
                            dbc.RadioItems(
                                id="hosting-filter-radio",
                                options=[
                                    {"label": "1. All", "value": "all"},
                                    {"label": "2. On-Premise (Physical & VMs)", "value": "onprem"},
                                    {"label": "3. Cloud (Azure & AWS)", "value": "cloud"},
                                ],
                                value=filter_mode,
                                inline=True,
                                style={"fontSize": "0.82rem"},
                            ),
                        ],
                        className="mt-1",
                    ),
                ],
                style={"backgroundColor": T.BG_CARD, "borderBottom": f"1px solid {T.BORDER}"},
            ),
            dbc.CardBody(
                [
                    # Cloud & On-Prem summary indicators
                    html.Div(
                        [
                            dbc.Badge(
                                f"☁️ Cloud (Azure & AWS): {cloud_total:,} ({cloud_pct:.1f}%)",
                                color="info",
                                className="me-2",
                                style={"fontSize": "0.78rem", "padding": "5px 10px"},
                            ),
                            dbc.Badge(
                                f"🏢 On-Premise (Physical & VMs): {onprem_total:,} ({onprem_pct:.1f}%)",
                                color="secondary",
                                style={"fontSize": "0.78rem", "padding": "5px 10px"},
                            ),
                        ],
                        className="mb-2 text-center",
                    ),
                    dcc.Graph(
                        id="hosting-donut-graph",
                        figure=hosting_fig,
                        config={"displayModeBar": False},
                        style={"height": "250px"},
                    ),
                ],
                style={"padding": "10px"},
            ),
        ],
        style={"backgroundColor": T.BG_CARD, "border": f"1px solid {T.BORDER}", "borderRadius": "8px", "height": "100%"},
    )


def build_hosting_box_2(server_data: dict, filter_mode: str = "all") -> dbc.Card:
    """
    Box 2: Organization-wise Stacked Column Bar Graph Display.
    """
    org_dist = server_data.get("org_distribution", [])
    bar_fig = charts.hosting_org_stacked_bar(org_dist, filter_mode=filter_mode)

    return dbc.Card(
        [
            dbc.CardHeader(
                html.Span([
                    html.Span("🏢", style={"marginRight": "8px"}),
                    html.Span("Organization-Wise Hosting Distribution", style=T.FONT_SECTION_TITLE),
                    dbc.Badge("Stacked Columns", color="secondary", className="ms-2"),
                ]),
                style={"backgroundColor": T.BG_CARD, "borderBottom": f"1px solid {T.BORDER}"},
            ),
            dbc.CardBody(
                [
                    dcc.Graph(
                        id="hosting-stacked-bar-graph",
                        figure=bar_fig,
                        config={"displayModeBar": False},
                        style={"height": "285px"},
                    ),
                ],
                style={"padding": "10px"},
            ),
        ],
        style={"backgroundColor": T.BG_CARD, "border": f"1px solid {T.BORDER}", "borderRadius": "8px", "height": "100%"},
    )


def build_server_hosting_panel(server_data: dict, filter_mode: str = "all") -> dbc.Row:
    """
    Renders Box 1 and Box 2 side by side.
    """
    return dbc.Row(
        [
            dbc.Col(build_hosting_box_1(server_data, filter_mode=filter_mode), lg=6, md=12, className="mb-3"),
            dbc.Col(build_hosting_box_2(server_data, filter_mode=filter_mode), lg=6, md=12, className="mb-3"),
        ],
        className="g-3",
    )
