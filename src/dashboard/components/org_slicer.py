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
    **kwargs: Any,
) -> dbc.Card:
    """
    Renders the executive multi-select dropdown filter control bar across 2 comfortable rows.
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

    # 2. Location / Country Dropdown Options & Value
    country_display_map = {
        "USA": "🇺🇸 United States (USA)",
        "US": "🇺🇸 United States",
        "GBR": "🇬🇧 United Kingdom (GBR)",
        "UK": "🇬🇧 United Kingdom",
        "DEU": "🇩🇪 Germany (DEU)",
        "JPN": "🇯🇵 Japan (JPN)",
        "IND": "🇮🇳 India (IND)",
        "AUS": "🇦🇺 Australia (AUS)",
        "CAN": "🇨🇦 Canada (CAN)",
        "BRA": "🇧🇷 Brazil (BRA)",
        "SGP": "🇸🇬 Singapore (SGP)",
        "FRA": "🇫🇷 France (FRA)",
        "NLD": "🇳🇱 Netherlands (NLD)",
        "IRL": "🇮🇪 Ireland (IRL)",
    }

    clean_loc_opts = [
        {"label": country_display_map.get(loc, f"📍 {loc}"), "value": loc}
        for loc in sorted(location_options)
        if loc not in ["all", "All Locations", "All Countries", None, ""]
    ]

    if isinstance(active_location, (list, tuple, set)):
        cur_loc_val = [str(x) for x in active_location if x not in ["all", "All Locations", "All Countries", None, ""]]
    elif active_location and active_location not in ["all", "All Locations", "All Countries", None, ""]:
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
    raw_role_opts = role_options if role_options is not None else [
        "Domain Controller",
        "Database Server",
        "Web Server",
        "File Server",
        "Application Server",
        "Backup Server",
        "General Server",
        "Workstation",
    ]
    clean_role_opts = [
        {"label": f"🛡️ {r}", "value": r}
        for r in raw_role_opts
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

    # Dropdown common style (comfortable contrast in dark mode without eye-stressing glare)
    dd_style = {
        "color": "#0F172A" if theme_mode == "light" else "#94A3B8",
        "fontSize": "0.80rem",
    }

    return dbc.Card(
        dbc.CardBody(
            dbc.Row(
                [
                    # 1. Organization Dropdown
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    html.Span("🏢 Organization", style={**T.FONT_KPI_LABEL, "fontSize": "0.70rem", "color": T.ACCENT_CYAN}),
                                    dbc.Badge(f"{len(cur_org_val)}", color="info", className="ms-1", style={"fontSize": "0.62rem", "padding": "2px 5px"}) if cur_org_val else None,
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
                        className="col-xl col-lg-4 col-md-6 col-12 mb-1",
                    ),

                    # 2. Country / Location Dropdown
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    html.Span("🌍 Country / Location", style={**T.FONT_KPI_LABEL, "fontSize": "0.70rem", "color": T.ACCENT_PURPLE}),
                                    dbc.Badge(f"{len(cur_loc_val)}", color="primary", className="ms-1", style={"fontSize": "0.62rem", "padding": "2px 5px"}) if cur_loc_val else None,
                                ],
                                className="d-flex align-items-center mb-1",
                            ),
                            dcc.Dropdown(
                                id="filter-location-dropdown",
                                options=clean_loc_opts,
                                value=cur_loc_val,
                                multi=True,
                                placeholder="All Countries / Locations...",
                                className="filter-dd",
                                style=dd_style,
                            ),
                        ],
                        className="col-xl col-lg-4 col-md-6 col-12 mb-1",
                    ),

                    # 3. OS Family Dropdown
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    html.Span("💻 OS Family", style={**T.FONT_KPI_LABEL, "fontSize": "0.70rem", "color": T.ACCENT_TEAL}),
                                    dbc.Badge(f"{len(cur_os_val)}", color="success", className="ms-1", style={"fontSize": "0.62rem", "padding": "2px 5px"}) if cur_os_val else None,
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
                        className="col-xl col-lg-4 col-md-4 col-12 mb-1",
                    ),

                    # 4. Device Roles Dropdown
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    html.Span("🛡️ Device Role", style={**T.FONT_KPI_LABEL, "fontSize": "0.70rem", "color": T.ACCENT_BLUE}),
                                    dbc.Badge(f"{len(cur_roles_val)}", color="secondary", className="ms-1", style={"fontSize": "0.62rem", "padding": "2px 5px"}) if cur_roles_val else None,
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
                        className="col-xl col-lg-4 col-md-4 col-12 mb-1",
                    ),

                    # 5. Patch Scope Dropdown
                    dbc.Col(
                        [
                            html.Div(
                                html.Span("🩹 Patch Scope", style={**T.FONT_KPI_LABEL, "fontSize": "0.70rem", "color": T.RAG_AMBER}),
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
                        className="col-xl col-lg-4 col-md-4 col-12 mb-1",
                    ),

                    # 6. Reset Filters Button
                    dbc.Col(
                        [
                            html.Div(
                                html.Span("‎", style={"fontSize": "0.70rem", "visibility": "hidden", "lineHeight": "1"}),
                                className="mb-1",
                            ),
                            dbc.Button(
                                "↺ Reset",
                                id="reset-filters-btn",
                                color="secondary",
                                outline=True,
                                size="sm",
                                title="Clear all filters back to Global Overview",
                                style={
                                    "height": "34px",
                                    "fontSize": "0.80rem",
                                    "padding": "4px 12px",
                                    "borderColor": p["border"],
                                    "whiteSpace": "nowrap",
                                    "fontWeight": "600",
                                    "display": "flex",
                                    "alignItems": "center",
                                    "justifyContent": "center",
                                },
                            ),
                        ],
                        className="col-xl-auto col-lg-auto col-md-auto col-12 mb-1 d-flex flex-column justify-content-end",
                    ),
                ],
                className="g-2 align-items-end",
            ),
            style={"padding": "8px 14px", "backgroundColor": p["bg_card"]},
        ),
        className="filter-bar-card",
        style={
            "backgroundColor": p["bg_card"],
            "border": f"1px solid {p['border']}",
            "borderRadius": "8px",
            "marginBottom": "12px",
            "boxShadow": "0 2px 8px rgba(0,0,0,0.08)",
        },
    )
