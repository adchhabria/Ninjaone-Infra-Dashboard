"""
Separate Windows & Linux Operating System Distribution Panels.

Renders separate donut cards:
- If both Windows and Linux exist: side by side (lg=6)
- If only Windows machines selected: Linux card is removed and Windows card expands (lg=12) with animation
- If only Linux machines selected: Windows card is removed and Linux card expands (lg=12) with animation
"""

from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import dcc, html

from src.dashboard import charts, theme as T


def build_windows_os_panel(os_data: dict, theme_mode: str = "dark") -> dbc.Card:
    """
    Dedicated card for Windows Operating System Distribution.
    """
    p = T.get_theme_palette(theme_mode)
    win_counts = os_data.get("windows_version_counts", {})
    win_fig = charts.windows_os_donut(win_counts, theme_mode=theme_mode)
    if hasattr(win_fig, "update_layout"):
        win_fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        win_fig.update_layout(font_color=p["text_primary"])
    win_total = sum(win_counts.values())

    return dbc.Card(
        [
            dbc.CardHeader(
                html.Span([
                    html.Span("🪟", style={"marginRight": "8px"}),
                    html.Span("Windows Operating Systems", style={**T.FONT_SECTION_TITLE, "color": p["text_primary"]}),
                    dbc.Badge(f"{win_total:,} Devices", color="primary", className="ms-2"),
                ]),
                style={"backgroundColor": p["bg_card"], "borderBottom": f"1px solid {p['border']}"},
            ),
            dbc.CardBody(
                [
                    dcc.Graph(figure=win_fig, config={"displayModeBar": False}, style={"height": "270px"}),
                ],
                style={"padding": "12px", "backgroundColor": p["bg_card"]},
            ),
        ],
        style={
            "backgroundColor": p["bg_card"],
            "border": f"1px solid {p['border']}",
            "borderRadius": "8px",
            "height": "100%",
            "transition": "all 0.35s ease-in-out",
        },
    )


def build_linux_os_panel(os_data: dict, theme_mode: str = "dark") -> dbc.Card:
    """
    Dedicated card for Linux Operating System Distribution.
    """
    p = T.get_theme_palette(theme_mode)
    linux_counts = os_data.get("linux_version_counts", {})
    linux_fig = charts.linux_os_donut(linux_counts, theme_mode=theme_mode)
    if hasattr(linux_fig, "update_layout"):
        linux_fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        linux_fig.update_layout(font_color=p["text_primary"])
    linux_total = sum(linux_counts.values())

    return dbc.Card(
        [
            dbc.CardHeader(
                html.Span([
                    html.Span("🐧", style={"marginRight": "8px"}),
                    html.Span("Linux Operating Systems", style={**T.FONT_SECTION_TITLE, "color": p["text_primary"]}),
                    dbc.Badge(f"{linux_total:,} Devices", color="success", className="ms-2"),
                ]),
                style={"backgroundColor": p["bg_card"], "borderBottom": f"1px solid {p['border']}"},
            ),
            dbc.CardBody(
                [
                    dcc.Graph(figure=linux_fig, config={"displayModeBar": False}, style={"height": "270px"}),
                ],
                style={"padding": "12px", "backgroundColor": p["bg_card"]},
            ),
        ],
        style={
            "backgroundColor": p["bg_card"],
            "border": f"1px solid {p['border']}",
            "borderRadius": "8px",
            "height": "100%",
            "transition": "all 0.35s ease-in-out",
        },
    )


def build_os_panel(os_data: dict, theme_mode: str = "dark") -> dbc.Row:
    """
    Renders operating system distribution donut panels.
    - If only Windows machines: Linux box is omitted, Windows box expands to full width (lg=12).
    - If only Linux machines: Windows box is omitted, Linux box expands to full width (lg=12).
    - If both exist: Rendered side by side (lg=6 each).
    """
    win_counts = os_data.get("windows_version_counts", {})
    linux_counts = os_data.get("linux_version_counts", {})
    win_total = sum(win_counts.values())
    linux_total = sum(linux_counts.values())

    cols = []
    if win_total > 0 and linux_total == 0:
        # Only Windows: expand to full width with smooth animation
        cols.append(
            dbc.Col(
                build_windows_os_panel(os_data, theme_mode=theme_mode),
                lg=12,
                md=12,
                className="mb-3 os-donut-col-expanded",
            )
        )
    elif linux_total > 0 and win_total == 0:
        # Only Linux: expand to full width with smooth animation
        cols.append(
            dbc.Col(
                build_linux_os_panel(os_data, theme_mode=theme_mode),
                lg=12,
                md=12,
                className="mb-3 os-donut-col-expanded",
            )
        )
    elif win_total > 0 or linux_total > 0:
        # Both present: side-by-side
        cols.append(
            dbc.Col(build_windows_os_panel(os_data, theme_mode=theme_mode), lg=6, md=12, className="mb-3 os-donut-col")
        )
        cols.append(
            dbc.Col(build_linux_os_panel(os_data, theme_mode=theme_mode), lg=6, md=12, className="mb-3 os-donut-col")
        )
    else:
        # Zero state: render single expanded card
        cols.append(
            dbc.Col(build_windows_os_panel(os_data, theme_mode=theme_mode), lg=12, md=12, className="mb-3")
        )

    return dbc.Row(cols, className="g-3")
