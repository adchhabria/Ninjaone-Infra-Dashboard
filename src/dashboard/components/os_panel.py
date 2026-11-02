"""
Operating System Landscape & Patch Category Breakdown Panels.

Renders responsive donut cards:
- If both Windows and Linux exist: 3 columns (lg=4 Windows OS, lg=4 Linux OS, lg=4 Patch Category Breakdown)
- If only Windows machines: Linux card omitted, Windows card adapts (lg=8) alongside Patch Category Breakdown (lg=4)
- If only Linux machines: Windows card omitted, Linux card adapts (lg=8) alongside Patch Category Breakdown (lg=4)
- If zero state: Windows card (lg=6) alongside Patch Category Breakdown (lg=6)
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


def build_patch_category_panel(type_counts: dict | None = None, theme_mode: str = "dark") -> dbc.Card:
    """
    Dedicated card for Patch Category Breakdown (OS Security Updates vs 3rd-Party Applications).
    """
    p = T.get_theme_palette(theme_mode)
    counts = type_counts or {}
    type_fig = charts.patch_type_donut(counts, theme_mode=theme_mode)
    total_items = sum(counts.values())

    return dbc.Card(
        [
            dbc.CardHeader(
                html.Span([
                    html.Span("📦", style={"marginRight": "8px"}),
                    html.Span("Patch Category Breakdown", style={**T.FONT_SECTION_TITLE, "color": p["text_primary"]}),
                    dbc.Badge(f"{total_items:,} Patches", color="info", className="ms-2"),
                ]),
                style={"backgroundColor": p["bg_card"], "borderBottom": f"1px solid {p['border']}"},
            ),
            dbc.CardBody(
                [
                    dcc.Graph(
                        id="patch-type-donut",
                        figure=type_fig,
                        config={"displayModeBar": False},
                        style={"height": "270px"},
                    ),
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


def build_os_panel(os_data: dict, type_counts: dict | None = None, theme_mode: str = "dark") -> dbc.Row:
    """
    Renders operating system distribution and patch category breakdown panels.
    - If both Windows and Linux exist: 3 columns (lg=4 each).
    - If only Windows machines: Linux box omitted, Windows box adapts (lg=8) alongside Category Breakdown (lg=4).
    - If only Linux machines: Windows box omitted, Linux box adapts (lg=8) alongside Category Breakdown (lg=4).
    - Zero state: Windows box (lg=6) alongside Category Breakdown (lg=6).
    """
    win_counts = os_data.get("windows_version_counts", {})
    linux_counts = os_data.get("linux_version_counts", {})
    win_total = sum(win_counts.values())
    linux_total = sum(linux_counts.values())

    cols = []
    category_card = build_patch_category_panel(type_counts=type_counts, theme_mode=theme_mode)

    if win_total > 0 and linux_total == 0:
        # Only Windows + Patch Category Breakdown
        cols.append(
            dbc.Col(
                build_windows_os_panel(os_data, theme_mode=theme_mode),
                lg=8,
                md=12,
                className="mb-3 os-donut-col-expanded",
            )
        )
        cols.append(
            dbc.Col(
                category_card,
                lg=4,
                md=12,
                className="mb-3",
            )
        )
    elif linux_total > 0 and win_total == 0:
        # Only Linux + Patch Category Breakdown
        cols.append(
            dbc.Col(
                build_linux_os_panel(os_data, theme_mode=theme_mode),
                lg=8,
                md=12,
                className="mb-3 os-donut-col-expanded",
            )
        )
        cols.append(
            dbc.Col(
                category_card,
                lg=4,
                md=12,
                className="mb-3",
            )
        )
    elif win_total > 0 or linux_total > 0:
        # Both present: 3 columns side-by-side
        cols.append(
            dbc.Col(build_windows_os_panel(os_data, theme_mode=theme_mode), lg=4, md=12, className="mb-3 os-donut-col")
        )
        cols.append(
            dbc.Col(build_linux_os_panel(os_data, theme_mode=theme_mode), lg=4, md=12, className="mb-3 os-donut-col")
        )
        cols.append(
            dbc.Col(category_card, lg=4, md=12, className="mb-3")
        )
    else:
        # Zero state: Windows + Patch Category Breakdown
        cols.append(
            dbc.Col(build_windows_os_panel(os_data, theme_mode=theme_mode), lg=6, md=12, className="mb-3")
        )
        cols.append(
            dbc.Col(category_card, lg=6, md=12, className="mb-3")
        )

    return dbc.Row(cols, className="g-3")
