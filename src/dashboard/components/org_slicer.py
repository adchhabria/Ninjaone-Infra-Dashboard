"""
Multi-Dimensional Dropdown Filter Bar Component.

Replaces slicer buttons with interactive multi-select dropdown boxes:
1. 🏢 Organizations (Multi-Select Checkboxes)
2. 📍 Locations (Multi-Select Checkboxes)
3. 💻 OS Families (Multi-Select Checkboxes: Windows, Linux, macOS)
4. 🛡️ Device Roles (Multi-Select Checkboxes: Domain Controller, Database Server, etc.)
5. 🩹 Patch Scope (Both, OS Only, Software Only)
6. ↺ Reset Filters Button
"""

from __future__ import annotations

from typing import Any, Optional

import dash_bootstrap_components as dbc
from dash import dcc, html

from src.dashboard import theme as T


def build_org_slicer(
    org_options: list[dict],
    location_options: list[str],
    os_family_options: list[str],
    role_options: Optional[list[str]] = None,
    active_org_id: Any = None,
    active_location: Any = None,
    active_os_family: Any = None,
    active_roles: Any = None,
    active_patch_type: str = "both",
    theme_mode: str = "dark",
) -> dbc.Card:
    """
    Renders the executive multi-select dropdown filter control bar.
    """
    p = T.get_theme_palette(theme_mode)

    # 1. Organization Dropdown Options & Value
    clean_org_opts = []
    for o in org_options:
        v = str(o["value"])
        if v not in ["all", "All Organizations"]:
            clean_org_opts.append({"label": f"🏢 {o['label']}", "value": v})

    if isinstance(active_org_id, (list, tuple, set)):
        cur_org_val = [str(x) for x in active_org_id if str(x) not in ["all", "None", ""]]
    elif active_org_id and str(active_org_id) not in ["all", "None", ""]:
        cur_org_val = [str(active_org_id)]
    else:
        cur_org_val = []

    # 2. Location Dropdown Options & Value
    clean_loc_opts = [
        {"label": f"📍 {loc}", "value": loc}
        for loc in sorted(location_options)
        if loc not in ["all", "All Locations", None, ""]
    ]

    if isinstance(active_location, (list, tuple, set)):
        cur_loc_val = [str(x) for x in active_location if x not in ["all", "All Locations", None, ""]]
    elif active_location and active_location not in ["all", "All Locations", None, ""]:
        cur_loc_val = [str(active_location)]
    else:
        cur_loc_val = []

    # 3. OS Family Dropdown Options & Value
    def _os_icon(fam: str) -> str:
        f = fam.lower()
        if "win" in f:
            return "🪟"
        if "lin" in f:
            return "🐧"
        if "mac" in f or "apple" in f:
            return "🍏"
        return "💻"

    clean_os_opts = [
        {"label": f"{_os_icon(os_fam)} {os_fam}", "value": os_fam}
        for os_fam in (os_family_options or ["Windows", "Linux", "macOS"])
        if os_fam not in ["all", "All OS Families", None, ""]
    ]

    if isinstance(active_os_family, (list, tuple, set)):
        cur_os_val = [str(x) for x in active_os_family if x not in ["all", "All OS Families", None, ""]]
    elif active_os_family and active_os_family not in ["all", "All OS Families", None, ""]:
        cur_os_val = [str(active_os_family)]
    else:
        cur_os_val = []

    # 4. Device Role Dropdown Options & Value
    clean_role_opts = [
        {"label": f"🛡️ {r}", "value": r}
        for r in (role_options or [
            "Domain Controller",
            "Database Server",
            "Web Server",
            "File Server",
            "Application Server",
            "Backup Server",
            "General Server",
            "Workstation",
        ])
        if r not in ["all", "All Roles", None, ""]
    ]

    if isinstance(active_roles, (list, tuple, set)):
        cur_roles_val = [str(x) for x in active_roles if x not in ["all", "All Roles", None, ""]]
    elif active_roles and active_roles not in ["all", "All Roles", None, ""]:
        cur_roles_val = [str(active_roles)]
    else:
        cur_roles_val = []

    # 5. Patch Scope Dropdown Options & Value
    patch_type_opts = [
        {"label": "📦 Both (OS + Software)", "value": "both"},
        {"label": "💻 OS Patches Only", "value": "os"},
        {"label": "🧩 Software Patches Only", "value": "software"},
    ]
    cur_patch_type = str(active_patch_type or "both").lower()

    # Dropdown common style
    dd_style = {
        "color": p["text_primary"],
        "fontSize": "0.85rem",
    }

    return dbc.Card(
        dbc.CardBody(
            [
                # Row 1: Organizations, Locations, OS Families
                dbc.Row(
                    [
                        # Organization Multi-Select
                        dbc.Col(
                            [
                                html.Div(
                                    [
                                        html.Span("🏢 Organization", style={**T.FONT_KPI_LABEL, "color": T.ACCENT_CYAN}),
                                        dbc.Badge(f"{len(cur_org_val)} selected", color="info", className="ms-1", style={"fontSize": "0.68rem"}) if cur_org_val else None,
                                    ],
                                    className="d-flex align-items-center mb-1",
                                ),
                                dcc.Dropdown(
                                    id="filter-org-dropdown",
                                    options=clean_org_opts,
                                    value=cur_org_val,
                                    multi=True,
                                    placeholder="All Organizations...",
                                    className="filter-dd",
                                    style=dd_style,
                                ),
                            ],
                            lg=4,
                            md=6,
                            sm=12,
                            className="mb-2",
                        ),
                        # Location Multi-Select
                        dbc.Col(
                            [
                                html.Div(
                                    [
                                        html.Span("📍 Location", style={**T.FONT_KPI_LABEL, "color": T.ACCENT_PURPLE}),
                                        dbc.Badge(f"{len(cur_loc_val)} selected", color="primary", className="ms-1", style={"fontSize": "0.68rem"}) if cur_loc_val else None,
                                    ],
                                    className="d-flex align-items-center mb-1",
                                ),
                                dcc.Dropdown(
                                    id="filter-location-dropdown",
                                    options=clean_loc_opts,
                                    value=cur_loc_val,
                                    multi=True,
                                    placeholder="All Locations...",
                                    className="filter-dd",
                                    style=dd_style,
                                ),
                            ],
                            lg=4,
                            md=6,
                            sm=12,
                            className="mb-2",
                        ),
                        # OS Family Multi-Select
                        dbc.Col(
                            [
                                html.Div(
                                    [
                                        html.Span("💻 OS Family", style={**T.FONT_KPI_LABEL, "color": T.ACCENT_TEAL}),
                                        dbc.Badge(f"{len(cur_os_val)} selected", color="success", className="ms-1", style={"fontSize": "0.68rem"}) if cur_os_val else None,
                                    ],
                                    className="d-flex align-items-center mb-1",
                                ),
                                dcc.Dropdown(
                                    id="filter-os-dropdown",
                                    options=clean_os_opts,
                                    value=cur_os_val,
                                    multi=True,
                                    placeholder="All OS Families...",
                                    className="filter-dd",
                                    style=dd_style,
                                ),
                            ],
                            lg=4,
                            md=12,
                            sm=12,
                            className="mb-2",
                        ),
                    ],
                    className="g-3 mb-1",
                ),

                # Row 2: Device Roles, Patch Scope, Reset Button
                dbc.Row(
                    [
                        # Device Roles Multi-Select
                        dbc.Col(
                            [
                                html.Div(
                                    [
                                        html.Span("🛡️ Device Roles", style={**T.FONT_KPI_LABEL, "color": T.ACCENT_BLUE}),
                                        dbc.Badge(f"{len(cur_roles_val)} selected", color="secondary", className="ms-1", style={"fontSize": "0.68rem"}) if cur_roles_val else None,
                                    ],
                                    className="d-flex align-items-center mb-1",
                                ),
                                dcc.Dropdown(
                                    id="filter-roles-dropdown",
                                    options=clean_role_opts,
                                    value=cur_roles_val,
                                    multi=True,
                                    placeholder="All Device Roles...",
                                    className="filter-dd",
                                    style=dd_style,
                                ),
                            ],
                            lg=6,
                            md=12,
                            sm=12,
                            className="mb-1",
                        ),
                        # Patch Scope Dropdown
                        dbc.Col(
                            [
                                html.Div(
                                    html.Span("🩹 Patch Scope", style={**T.FONT_KPI_LABEL, "color": T.RAG_AMBER}),
                                    className="d-flex align-items-center mb-1",
                                ),
                                dcc.Dropdown(
                                    id="filter-patch-type-dropdown",
                                    options=patch_type_opts,
                                    value=cur_patch_type,
                                    multi=False,
                                    clearable=False,
                                    className="filter-dd",
                                    style=dd_style,
                                ),
                            ],
                            lg=4,
                            md=8,
                            sm=8,
                            className="mb-1",
                        ),
                        # Reset Filters Button
                        dbc.Col(
                            [
                                html.Div(
                                    html.Span("‎", style={"fontSize": "0.75rem", "visibility": "hidden"}),
                                    className="mb-1",
                                ),
                                dbc.Button(
                                    "↺ Reset Filters",
                                    id="reset-filters-btn",
                                    color="secondary",
                                    outline=True,
                                    size="sm",
                                    className="w-100",
                                    title="Clear all filters back to Global Overview",
                                    style={
                                        "fontSize": "0.85rem",
                                        "padding": "7px 14px",
                                        "borderColor": p["border"],
                                        "whiteSpace": "nowrap",
                                        "fontWeight": "600",
                                    },
                                ),
                            ],
                            lg=2,
                            md=4,
                            sm=4,
                            className="mb-1",
                        ),
                    ],
                    className="g-3 align-items-end",
                ),
            ],
            style={"padding": "14px 18px", "backgroundColor": p["bg_card"]},
        ),
        style={
            "backgroundColor": p["bg_card"],
            "border": f"1px solid {p['border']}",
            "borderRadius": "8px",
            "marginBottom": "16px",
            "boxShadow": "0 2px 10px rgba(0,0,0,0.12)",
        },
    )
