"""
Reboot Watchlist & Patch Failures Operations Component.

Inspired by ninjaone-patch-toolkit:
Features:
- Inventory of endpoints requiring reboot to complete patch installations
- Ledger of patch deployment failures with specific error codes
- Excel-style header filtering and multi-column sorting on all tables
- Operational actions: Trigger Remote Scan & Reboot
"""

from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import dash_table, html

from src.dashboard import theme as T


_REBOOT_COLUMNS = [
    {"name": "Device Name", "id": "name", "type": "text"},
    {"name": "Organization", "id": "org_name", "type": "text"},
    {"name": "Location", "id": "location", "type": "text"},
    {"name": "Region", "id": "region", "type": "text"},
    {"name": "Operating System", "id": "os", "type": "text"},
    {"name": "Uptime (Days)", "id": "uptime_days", "type": "numeric"},
    {"name": "Pending Patches", "id": "pending_count", "type": "numeric"},
    {"name": "Status", "id": "status", "type": "text"},
]

_FAILURE_COLUMNS = [
    {"name": "Device Name", "id": "device_name", "type": "text"},
    {"name": "Organization", "id": "org_name", "type": "text"},
    {"name": "Location", "id": "location", "type": "text"},
    {"name": "Region", "id": "region", "type": "text"},
    {"name": "Failed Update / KB", "id": "patch_name", "type": "text"},
    {"name": "Error Code", "id": "error_code", "type": "text"},
    {"name": "Last Attempt Date", "id": "failed_date", "type": "text"},
    {"name": "Retry Attempts", "id": "attempts", "type": "numeric"},
]


def build_reboot_failures_panel(sla_data: dict, theme_mode: str = "dark") -> html.Div:
    """
    Renders the Reboot Watchlist and Patch Failures operational tables with Excel filtering.
    """
    p = T.get_theme_palette(theme_mode)
    reboot_rows = sla_data.get("reboot_devices", [])
    failed_rows = sla_data.get("failed_patches", [])

    reboot_table = dash_table.DataTable(
        id="reboot-watchlist-table",
        columns=_REBOOT_COLUMNS,
        data=reboot_rows,
        sort_action="native",
        sort_mode="multi",
        filter_action="native",
        filter_options={"case": "insensitive", "placeholder_text": "🔍 Filter..."},
        page_size=8,
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
        style_data_conditional=[
            {"if": {"filter_query": "{uptime_days} > 30", "column_id": "uptime_days"}, "color": T.RAG_AMBER, "fontWeight": "600"},
            {"if": {"filter_query": "{uptime_days} > 60", "column_id": "uptime_days"}, "color": T.RAG_RED, "fontWeight": "700"},
            {"if": {"state": "active"}, "backgroundColor": p["bg_card_hover"], "border": f"1px solid {p['border']}"},
        ],
        style_filter={
            "backgroundColor": p["bg_card_hover"],
            "color": p["text_primary"],
            "border": f"1px solid {p['border']}",
            "fontSize": "0.80rem",
        },
    )

    failures_table = dash_table.DataTable(
        id="patch-failures-table",
        columns=_FAILURE_COLUMNS,
        data=failed_rows,
        sort_action="native",
        sort_mode="multi",
        filter_action="native",
        filter_options={"case": "insensitive", "placeholder_text": "🔍 Filter..."},
        page_size=8,
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
        style_data_conditional=[
            {"if": {"column_id": "error_code"}, "color": T.RAG_RED, "fontWeight": "600", "fontFamily": "monospace"},
            {"if": {"state": "active"}, "backgroundColor": p["bg_card_hover"], "border": f"1px solid {p['border']}"},
        ],
        style_filter={
            "backgroundColor": p["bg_card_hover"],
            "color": p["text_primary"],
            "border": f"1px solid {p['border']}",
            "fontSize": "0.80rem",
        },
    )

    return html.Div(
        [
            # Section 1: Pending Reboot Watchlist
            dbc.Card(
                [
                    dbc.CardHeader(
                        dbc.Row(
                            [
                                dbc.Col(
                                    html.Span([
                                        html.Span("🔄", style={"marginRight": "8px"}),
                                        html.Span("Endpoints Requiring Reboot", style={**T.FONT_SECTION_TITLE, "color": p["text_primary"]}),
                                        dbc.Badge(f"{len(reboot_rows)} Devices", color="warning" if reboot_rows else "success", className="ms-2"),
                                    ]),
                                    md=6,
                                ),
                                dbc.Col(
                                    html.Div(
                                        [
                                            dbc.Button("⚡ Trigger Bulk Reboot Action", id="trigger-bulk-reboot-btn", color="danger", outline=True, size="sm", style={"fontSize": "0.78rem"}),
                                        ],
                                        style={"textAlign": "right"},
                                    ),
                                    md=6,
                                ),
                            ],
                            align="center",
                        ),
                        style={"backgroundColor": p["bg_card"], "borderBottom": f"1px solid {p['border']}"},
                    ),
                    dbc.CardBody(reboot_table, style={"backgroundColor": p["bg_card"]}),
                ],
                style={"backgroundColor": p["bg_card"], "border": f"1px solid {p['border']}", "borderRadius": "8px", "marginBottom": "20px"},
            ),

            # Section 2: Patch Failures Ledger
            dbc.Card(
                [
                    dbc.CardHeader(
                        dbc.Row(
                            [
                                dbc.Col(
                                    html.Span([
                                        html.Span("❌", style={"marginRight": "8px"}),
                                        html.Span("Patch Deployment Failure Triage", style={**T.FONT_SECTION_TITLE, "color": p["text_primary"]}),
                                        dbc.Badge(f"{len(failed_rows)} Failed KBs", color="danger" if failed_rows else "success", className="ms-2"),
                                    ]),
                                    md=6,
                                ),
                                dbc.Col(
                                    html.Div(
                                        [
                                            dbc.Button("🔍 Trigger Fleet Patch Rescan", id="trigger-bulk-scan-btn", color="info", outline=True, size="sm", style={"fontSize": "0.78rem"}),
                                        ],
                                        style={"textAlign": "right"},
                                    ),
                                    md=6,
                                ),
                            ],
                            align="center",
                        ),
                        style={"backgroundColor": p["bg_card"], "borderBottom": f"1px solid {p['border']}"},
                    ),
                    dbc.CardBody(failures_table, style={"backgroundColor": p["bg_card"]}),
                ],
                style={"backgroundColor": p["bg_card"], "border": f"1px solid {p['border']}", "borderRadius": "8px", "marginBottom": "20px"},
            ),

            # Feedback Modal / Alert
            html.Div(id="action-feedback-container"),
        ]
    )
