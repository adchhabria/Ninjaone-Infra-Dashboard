"""
Interactive World Map Component.

Displays geographic distribution of infrastructure with circle marker diameters
scaled dynamically according to the volume of devices at each location.
Hovering over circles displays full compliance, device count, and organization breakdown.
"""

from __future__ import annotations

from typing import Optional

import dash_bootstrap_components as dbc
from dash import dcc, html

from src.dashboard import charts, theme as T


def build_map_panel(
    map_data: list[dict],
    active_region: Optional[str] = None,
) -> dbc.Card:
    """
    Renders World Map with clean header and proportional diameter bubbles.
    """
    fig = charts.world_map_chart(map_data, selected_region=active_region)

    total_locations = len(map_data)
    total_devs_mapped = sum(r.get("device_count", 0) for r in map_data)

    return dbc.Card(
        [
            dbc.CardHeader(
                dbc.Row(
                    [
                        dbc.Col(
                            html.Span(
                                [
                                    html.Span("🗺️", style={"marginRight": "8px"}),
                                    html.Span("Geographic Infrastructure & Compliance Map", style=T.FONT_SECTION_TITLE),
                                    dbc.Badge(f"{total_locations} Countries", color="secondary", className="ms-2"),
                                    dbc.Badge(f"{total_devs_mapped} Devices", color="primary", className="ms-1"),
                                ]
                            ),
                            md=8,
                        ),
                        dbc.Col(
                            html.Div(
                                html.Span("Hover over markers to inspect locations · Click marker to zoom",
                                          style={"fontSize": "0.78rem", "color": T.TEXT_MUTED}),
                                style={"textAlign": "right"},
                            ),
                            md=4,
                        ),
                    ],
                    align="center",
                ),
                style={"backgroundColor": T.BG_CARD, "borderBottom": f"1px solid {T.BORDER}"},
            ),
            dbc.CardBody(
                [
                    dcc.Graph(
                        id="world-map-graph",
                        figure=fig,
                        config={"displayModeBar": False, "scrollZoom": False},
                        style={"height": "320px"},
                    )
                ],
                style={"padding": "4px 12px 12px 12px"},
            ),
        ],
        style={
            "backgroundColor": T.BG_CARD,
            "border": f"1px solid {T.BORDER}",
            "borderRadius": "8px",
            "marginBottom": "20px",
        },
    )
