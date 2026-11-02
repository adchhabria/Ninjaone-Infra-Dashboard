"""
Patch Operations Details Hub Component.

Features:
- Table 1: Top 10 Servers with Max Pending Patches (Server Name, Org, Loc, OS name, Device Role, Approve patch Count)
- Table 2: Top 10 Patches Pending on Max Servers (Patch Name, Patch Type (Critical / Important), OS/Software type patch, Pending device count, Patch release date)
"""

from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import dash_table, html

from src.dashboard import theme as T

_TOP_SERVERS_COLUMNS = [
    {"name": "Server Name", "id": "name", "type": "text"},
    {"name": "Org", "id": "org_name", "type": "text"},
    {"name": "Loc", "id": "location", "type": "text"},
    {"name": "OS name", "id": "os_name", "type": "text"},
    {"name": "Device Role", "id": "device_role", "type": "text"},
    {"name": "Approve patch Count", "id": "approved_patch_count", "type": "numeric"},
]

_TOP_PATCHES_COLUMNS = [
    {"name": "Patch Name", "id": "patch_name", "type": "text"},
    {"name": "Patch Type (Critical / Important)", "id": "severity", "type": "text"},
    {"name": "OS/Software type patch", "id": "patch_category", "type": "text"},
    {"name": "Pending device count", "id": "pending_device_count", "type": "numeric"},
    {"name": "Patch release date", "id": "release_date", "type": "text"},
]


def build_sla_panel(sla_data: dict, patch_data: dict | None = None, theme_mode: str = "light") -> html.Div:
    """
    Renders Patch Operations Details:
    1. Top 10 Servers with Max Pending Patches
    2. Top 10 Patches Pending on Max Servers
    """
    p = T.get_theme_palette(theme_mode)
    sla_data = sla_data or {}
    top_servers = sla_data.get("top_servers_pending_patches", [])
    top_patches = sla_data.get("top_patches_pending_servers", [])

    server_style_conditional = [
        {
            "if": {"filter_query": "{approved_patch_count} > 0", "column_id": "approved_patch_count"},
            "color": T.RAG_RED,
            "fontWeight": "700",
        },
        {"if": {"state": "active"}, "backgroundColor": p["bg_card_hover"], "border": f"1px solid {p['border']}"},
    ]

    patch_style_conditional = [
        {
            "if": {"filter_query": "{severity} = 'CRITICAL' || {severity} = 'Critical'", "column_id": "severity"},
            "color": T.RAG_RED,
            "fontWeight": "700",
        },
        {
            "if": {"filter_query": "{severity} = 'IMPORTANT' || {severity} = 'Important'", "column_id": "severity"},
            "color": "#FF9800",
            "fontWeight": "600",
        },
        {
            "if": {"filter_query": "{pending_device_count} > 0", "column_id": "pending_device_count"},
            "fontWeight": "700",
            "color": p["text_primary"],
        },
        {"if": {"state": "active"}, "backgroundColor": p["bg_card_hover"], "border": f"1px solid {p['border']}"},
    ]

    top_servers_table = dash_table.DataTable(
        id="top-servers-pending-table",
        columns=_TOP_SERVERS_COLUMNS,
        data=top_servers,
        sort_action="native",
        sort_mode="multi",
        filter_action="native",
        filter_options={"case": "insensitive", "placeholder_text": "🔍 Filter..."},
        page_size=10,
        style_table={"overflowX": "auto"},
        style_header={
            "backgroundColor": p["bg_card_hover"],
            "color": p["text_primary"],
            "fontWeight": "600",
            "fontSize": "0.75rem",
            "textTransform": "uppercase",
            "letterSpacing": "0.06em",
            "border": f"1px solid {p['border']}",
        },
        style_cell={
            "backgroundColor": p["bg_card"],
            "color": p["text_primary"],
            "border": f"1px solid {p['border']}",
            "fontSize": "0.85rem",
            "padding": "8px 12px",
            "fontFamily": "Inter, -apple-system, sans-serif",
        },
        style_data_conditional=server_style_conditional,
        style_filter={
            "backgroundColor": p["bg_card_hover"],
            "color": p["text_primary"],
            "border": f"1px solid {p['border']}",
            "fontSize": "0.80rem",
        },
    )

    top_patches_table = dash_table.DataTable(
        id="top-patches-pending-table",
        columns=_TOP_PATCHES_COLUMNS,
        data=top_patches,
        sort_action="native",
        sort_mode="multi",
        filter_action="native",
        filter_options={"case": "insensitive", "placeholder_text": "🔍 Filter..."},
        page_size=10,
        style_table={"overflowX": "auto"},
        style_header={
            "backgroundColor": p["bg_card_hover"],
            "color": p["text_primary"],
            "fontWeight": "600",
            "fontSize": "0.75rem",
            "textTransform": "uppercase",
            "letterSpacing": "0.06em",
            "border": f"1px solid {p['border']}",
        },
        style_cell={
            "backgroundColor": p["bg_card"],
            "color": p["text_primary"],
            "border": f"1px solid {p['border']}",
            "fontSize": "0.85rem",
            "padding": "8px 12px",
            "fontFamily": "Inter, -apple-system, sans-serif",
        },
        style_data_conditional=patch_style_conditional,
        style_filter={
            "backgroundColor": p["bg_card_hover"],
            "color": p["text_primary"],
            "border": f"1px solid {p['border']}",
            "fontSize": "0.80rem",
        },
    )

    return html.Div(
        [
            # Table 1: Top 10 Servers with Max Pending Patches
            dbc.Card(
                [
                    dbc.CardHeader(
                        dbc.Row(
                            [
                                dbc.Col(
                                    html.Span([
                                        html.Span("🚨", style={"marginRight": "8px"}),
                                        html.Span(
                                            "Top 10 Servers with Max Pending Patches",
                                            style={**T.FONT_SECTION_TITLE, "color": p["text_primary"]},
                                        ),
                                        dbc.Badge(f"{len(top_servers)} Identified", color="danger", className="ms-2"),
                                        dbc.Badge("Action Required", color="warning", className="ms-1"),
                                    ]),
                                    md=8,
                                ),
                                dbc.Col(
                                    html.Div(
                                        [
                                            html.Span(
                                                "Prioritized remediation ledger based on approved pending patch count",
                                                style={"fontSize": "0.75rem", "color": p["text_muted"]},
                                            ),
                                        ],
                                        style={"textAlign": "right"},
                                    ),
                                    md=4,
                                ),
                            ],
                            align="center",
                        ),
                        style={"backgroundColor": p["bg_card"], "borderBottom": f"1px solid {p['border']}"},
                    ),
                    dbc.CardBody(top_servers_table, style={"backgroundColor": p["bg_card"]}),
                ],
                style={"backgroundColor": p["bg_card"], "border": f"1px solid {p['border']}", "borderRadius": "8px", "marginBottom": "24px"},
            ),

            # Table 2: Top 10 Patches Pending on Max Servers
            dbc.Card(
                [
                    dbc.CardHeader(
                        dbc.Row(
                            [
                                dbc.Col(
                                    html.Span([
                                        html.Span("🩹", style={"marginRight": "8px"}),
                                        html.Span(
                                            "Top 10 Patches Pending on Max Servers",
                                            style={**T.FONT_SECTION_TITLE, "color": p["text_primary"]},
                                        ),
                                        dbc.Badge(f"{len(top_patches)} Critical Items", color="primary", className="ms-2"),
                                        dbc.Badge("Fleet Blast Radius", color="danger", className="ms-1"),
                                    ]),
                                    md=8,
                                ),
                                dbc.Col(
                                    html.Div(
                                        [
                                            html.Span(
                                                "Ranked by pending server deployment blast radius across the fleet",
                                                style={"fontSize": "0.75rem", "color": p["text_muted"]},
                                            ),
                                        ],
                                        style={"textAlign": "right"},
                                    ),
                                    md=4,
                                ),
                            ],
                            align="center",
                        ),
                        style={"backgroundColor": p["bg_card"], "borderBottom": f"1px solid {p['border']}"},
                    ),
                    dbc.CardBody(top_patches_table, style={"backgroundColor": p["bg_card"]}),
                ],
                style={"backgroundColor": p["bg_card"], "border": f"1px solid {p['border']}", "borderRadius": "8px", "marginBottom": "20px"},
            ),
        ]
    )
