"""
Separate Windows & Linux Operating System Distribution Panels.

Renders 2 separate boxes side by side:
- Box A: Windows Operating Systems Donut
- Box B: Linux Operating Systems Donut
"""

from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import dcc, html

from src.dashboard import charts, theme as T


def build_windows_os_panel(os_data: dict) -> dbc.Card:
    """
    Dedicated card for Windows Operating System Distribution.
    """
    win_counts = os_data.get("windows_version_counts", {})
    win_fig = charts.windows_os_donut(win_counts)
    win_total = sum(win_counts.values())

    return dbc.Card(
        [
            dbc.CardHeader(
                html.Span([
                    html.Span("🪟", style={"marginRight": "8px"}),
                    html.Span("Windows Operating Systems", style=T.FONT_SECTION_TITLE),
                    dbc.Badge(f"{win_total:,} Devices", color="primary", className="ms-2"),
                ]),
                style={"backgroundColor": T.BG_CARD, "borderBottom": f"1px solid {T.BORDER}"},
            ),
            dbc.CardBody(
                [
                    dcc.Graph(figure=win_fig, config={"displayModeBar": False}, style={"height": "270px"}),
                ],
                style={"padding": "12px"},
            ),
        ],
        style={"backgroundColor": T.BG_CARD, "border": f"1px solid {T.BORDER}", "borderRadius": "8px", "height": "100%"},
    )


def build_linux_os_panel(os_data: dict) -> dbc.Card:
    """
    Dedicated card for Linux Operating System Distribution.
    """
    linux_counts = os_data.get("linux_version_counts", {})
    linux_fig = charts.linux_os_donut(linux_counts)
    linux_total = sum(linux_counts.values())

    return dbc.Card(
        [
            dbc.CardHeader(
                html.Span([
                    html.Span("🐧", style={"marginRight": "8px"}),
                    html.Span("Linux Operating Systems", style=T.FONT_SECTION_TITLE),
                    dbc.Badge(f"{linux_total:,} Devices", color="success", className="ms-2"),
                ]),
                style={"backgroundColor": T.BG_CARD, "borderBottom": f"1px solid {T.BORDER}"},
            ),
            dbc.CardBody(
                [
                    dcc.Graph(figure=linux_fig, config={"displayModeBar": False}, style={"height": "270px"}),
                ],
                style={"padding": "12px"},
            ),
        ],
        style={"backgroundColor": T.BG_CARD, "border": f"1px solid {T.BORDER}", "borderRadius": "8px", "height": "100%"},
    )


def build_os_panel(os_data: dict) -> dbc.Row:
    """
    Renders the 2 separate boxes side by side in a row.
    """
    return dbc.Row(
        [
            dbc.Col(build_windows_os_panel(os_data), lg=6, md=12, className="mb-3"),
            dbc.Col(build_linux_os_panel(os_data), lg=6, md=12, className="mb-3"),
        ],
        className="g-3",
    )
