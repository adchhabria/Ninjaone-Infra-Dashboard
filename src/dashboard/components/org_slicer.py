"""
Excel-style Multi-Dimensional Slicer Component.

Renders horizontal pill button rows for:
1. 🏢 Organizations
2. 📍 Locations (Cities / Sites)
3. 💻 OS Families (Windows / Linux / macOS)
"""

from __future__ import annotations

from typing import Optional

import dash_bootstrap_components as dbc
from dash import html

from src.dashboard import theme as T


def build_org_slicer(
    org_options: list[dict],
    location_options: list[str],
    os_family_options: list[str],
    active_org_id: Optional[int] = None,
    active_location: Optional[str] = None,
    active_os_family: Optional[str] = None,
) -> dbc.Card:
    """
    Renders an Excel Slicer bar with 3 stacked slicer rows:
    - Organization Slicer
    - Location Slicer
    - OS Family Slicer
    """
    # -----------------------------------------------------------------------
    # Row 1: Organization Buttons
    # -----------------------------------------------------------------------
    org_buttons = []
    is_all_org_active = active_org_id is None or str(active_org_id) == "all"
    org_buttons.append(
        dbc.Button(
            "🏢 All Organizations",
            id={"type": "org-slicer-btn", "index": "all"},
            color="primary" if is_all_org_active else "secondary",
            outline=not is_all_org_active,
            size="sm",
            className="me-2 mb-1",
            style={
                "fontSize": "0.80rem",
                "fontWeight": "600" if is_all_org_active else "400",
                "borderRadius": "20px",
                "padding": "4px 12px",
            },
        )
    )

    for opt in org_options:
        val = opt["value"]
        if val == "all":
            continue
        label = opt["label"]
        is_active = str(active_org_id) == str(val)

        org_buttons.append(
            dbc.Button(
                label,
                id={"type": "org-slicer-btn", "index": str(val)},
                color="primary" if is_active else "dark",
                outline=not is_active,
                size="sm",
                className="me-2 mb-1",
                style={
                    "fontSize": "0.78rem",
                    "fontWeight": "600" if is_active else "400",
                    "borderRadius": "20px",
                    "padding": "4px 11px",
                    "borderColor": T.ACCENT_BLUE if is_active else T.BORDER,
                    "backgroundColor": T.ACCENT_BLUE if is_active else T.BG_CARD_HOVER,
                    "color": T.TEXT_PRIMARY,
                },
            )
        )

    # -----------------------------------------------------------------------
    # Row 2: Location Buttons
    # -----------------------------------------------------------------------
    loc_buttons = []
    is_all_loc_active = active_location is None or active_location in ["all", "All Locations"]
    loc_buttons.append(
        dbc.Button(
            "📍 All Locations",
            id={"type": "location-slicer-btn", "index": "all"},
            color="info" if is_all_loc_active else "secondary",
            outline=not is_all_loc_active,
            size="sm",
            className="me-2 mb-1",
            style={
                "fontSize": "0.80rem",
                "fontWeight": "600" if is_all_loc_active else "400",
                "borderRadius": "20px",
                "padding": "4px 12px",
            },
        )
    )

    for loc in location_options:
        is_active = active_location == loc
        loc_buttons.append(
            dbc.Button(
                loc,
                id={"type": "location-slicer-btn", "index": loc},
                color="info" if is_active else "dark",
                outline=not is_active,
                size="sm",
                className="me-2 mb-1",
                style={
                    "fontSize": "0.78rem",
                    "fontWeight": "600" if is_active else "400",
                    "borderRadius": "20px",
                    "padding": "4px 11px",
                    "borderColor": T.ACCENT_CYAN if is_active else T.BORDER,
                    "backgroundColor": T.ACCENT_CYAN if is_active else T.BG_CARD_HOVER,
                    "color": "#000" if is_active else T.TEXT_PRIMARY,
                },
            )
        )

    # -----------------------------------------------------------------------
    # Row 3: OS Family Buttons
    # -----------------------------------------------------------------------
    os_buttons = []
    is_all_os_active = active_os_family is None or active_os_family in ["all", "All OS Families"]
    os_buttons.append(
        dbc.Button(
            "💻 All OS Families",
            id={"type": "os-family-slicer-btn", "index": "all"},
            color="success" if is_all_os_active else "secondary",
            outline=not is_all_os_active,
            size="sm",
            className="me-2 mb-1",
            style={
                "fontSize": "0.80rem",
                "fontWeight": "600" if is_all_os_active else "400",
                "borderRadius": "20px",
                "padding": "4px 12px",
            },
        )
    )

    for os_fam in os_family_options:
        is_active = active_os_family == os_fam
        os_buttons.append(
            dbc.Button(
                os_fam,
                id={"type": "os-family-slicer-btn", "index": os_fam},
                color="success" if is_active else "dark",
                outline=not is_active,
                size="sm",
                className="me-2 mb-1",
                style={
                    "fontSize": "0.78rem",
                    "fontWeight": "600" if is_active else "400",
                    "borderRadius": "20px",
                    "padding": "4px 11px",
                    "borderColor": T.RAG_GREEN if is_active else T.BORDER,
                    "backgroundColor": T.RAG_GREEN if is_active else T.BG_CARD_HOVER,
                    "color": "#000" if is_active else T.TEXT_PRIMARY,
                },
            )
        )

    return dbc.Card(
        dbc.CardBody(
            [
                # Row 1: Org Slicer
                html.Div(
                    [
                        html.Span("🏢 Organization Slicer", style={
                            **T.FONT_KPI_LABEL, "minWidth": "165px", "color": T.ACCENT_CYAN, "lineHeight": "30px",
                        }),
                        html.Div(org_buttons, style={"display": "flex", "flexWrap": "wrap", "alignItems": "center"}),
                    ],
                    style={"display": "flex", "flexWrap": "wrap", "alignItems": "center", "marginBottom": "8px"},
                ),
                html.Hr(style={"borderColor": T.BORDER, "margin": "6px 0 8px 0"}),

                # Row 2: Location Slicer
                html.Div(
                    [
                        html.Span("📍 Location Slicer", style={
                            **T.FONT_KPI_LABEL, "minWidth": "165px", "color": T.ACCENT_PURPLE, "lineHeight": "30px",
                        }),
                        html.Div(loc_buttons, style={"display": "flex", "flexWrap": "wrap", "alignItems": "center"}),
                    ],
                    style={"display": "flex", "flexWrap": "wrap", "alignItems": "center", "marginBottom": "8px"},
                ),
                html.Hr(style={"borderColor": T.BORDER, "margin": "6px 0 8px 0"}),

                # Row 3: OS Family Slicer
                html.Div(
                    [
                        html.Span("💻 OS Family Slicer", style={
                            **T.FONT_KPI_LABEL, "minWidth": "165px", "color": T.ACCENT_TEAL, "lineHeight": "30px",
                        }),
                        html.Div(os_buttons, style={"display": "flex", "flexWrap": "wrap", "alignItems": "center"}),
                    ],
                    style={"display": "flex", "flexWrap": "wrap", "alignItems": "center"},
                ),
            ],
            style={"padding": "12px 16px"},
        ),
        style={
            "backgroundColor": T.BG_CARD,
            "border": f"1px solid {T.BORDER}",
            "borderRadius": "8px",
            "marginBottom": "16px",
        },
    )
