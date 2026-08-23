"""
OS Landscape Panel — Separate Windows & Linux Distribution Donut Charts.
"""

from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import dcc, html

from src.dashboard import charts, theme as T


def build_os_panel(os_data: dict) -> dbc.Card:
    """
    Renders 2 separate donut charts for Windows and Linux OS breakdowns.
    """
    win_counts = os_data.get("windows_version_counts", {})
    linux_counts = os_data.get("linux_version_counts", {})

    win_fig = charts.windows_os_donut(win_counts)
    linux_fig = charts.linux_os_donut(linux_counts)

    win_total = sum(win_counts.values())
    linux_total = sum(linux_counts.values())

    return dbc.Card(
        [
            dbc.CardHeader(
                html.Span([
                    html.Span("💻", style={"marginRight": "8px"}),
                    html.Span("Operating System Landscape (Windows & Linux)", style=T.FONT_SECTION_TITLE),
                    dbc.Badge(f"{win_total} Windows", color="primary", className="ms-2"),
                    dbc.Badge(f"{linux_total} Linux", color="success", className="ms-1"),
                ]),
                style={"backgroundColor": T.BG_CARD, "borderBottom": f"1px solid {T.BORDER}"},
            ),
            dbc.CardBody(
                [
                    dbc.Row(
                        [
                            dbc.Col(dcc.Graph(figure=win_fig, config={"displayModeBar": False}, style={"height": "270px"}), md=6),
                            dbc.Col(dcc.Graph(figure=linux_fig, config={"displayModeBar": False}, style={"height": "270px"}), md=6),
                        ],
                        className="g-3",
                    ),
                ],
                style={"padding": "12px"},
            ),
        ],
        style={"backgroundColor": T.BG_CARD, "border": f"1px solid {T.BORDER}", "borderRadius": "8px", "height": "100%"},
    )
