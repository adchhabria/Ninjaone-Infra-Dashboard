"""
Patch Operations & SLA Aging Hub Component.

Inspired by ninjaone-patch-toolkit:
Features:
- SLA Aging Backlog Bar Chart (<7d, 8-30d, 31-90d, >90d)
- OS Security Updates vs 3rd-Party Applications Donut
- Granular Patch Inventory DataTable with SLA Badges, Multi-Column Sorting & Excel-Style Column Filters
"""

from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import dash_table, dcc, html

from src.dashboard import charts, theme as T


_SERVER_COMPLIANCE_COLUMNS = [
    {"name": "Server Name", "id": "name", "type": "text"},
    {"name": "Organization", "id": "org_name", "type": "text"},
    {"name": "Location", "id": "location", "type": "text"},
    {"name": "Operating System", "id": "os", "type": "text"},
    {"name": "Approved Patch Count", "id": "approved_patch_count", "type": "numeric"},
    {"name": "Approved Software Count", "id": "approved_software_count", "type": "numeric"},
    {"name": "Compliance Status", "id": "status", "type": "text"},
]


_PATCH_COLUMNS = [
    {"name": "Device Name", "id": "device_name", "type": "text"},
    {"name": "Organization", "id": "org_name", "type": "text"},
    {"name": "Location", "id": "location", "type": "text"},
    {"name": "Region", "id": "region", "type": "text"},
    {"name": "Patch / KB Name", "id": "patch_name", "type": "text"},
    {"name": "Type", "id": "patch_type", "type": "text"},
    {"name": "Severity", "id": "severity", "type": "text"},
    {"name": "Age (Days)", "id": "age_days", "type": "numeric"},
    {"name": "SLA Bracket", "id": "sla_bucket", "type": "text"},
    {"name": "Status", "id": "status", "type": "text"},
]


def build_sla_panel(sla_data: dict, patch_data: dict | None = None) -> html.Div:
    """
    Renders Server Compliance Table (Approved Patch & Software count),
    SLA aging analysis, patch category breakdown, and inventory grid with Excel filtering.
    """
    patch_data = patch_data or {}
    server_rows = patch_data.get("server_compliance_table", [])
    server_compliant = patch_data.get("server_compliant_count", sum(1 for r in server_rows if r.get("status") == "Compliant"))
    server_non_compliant = patch_data.get("server_non_compliant_count", len(server_rows) - server_compliant)
    server_total = patch_data.get("server_total_count", len(server_rows))
    server_pct = patch_data.get("server_compliance_pct", round(server_compliant / server_total * 100, 1) if server_total > 0 else 100.0)

    server_style_data_conditional = [
        {
            "if": {"filter_query": "{status} = 'Compliant'", "column_id": "status"},
            "color": T.RAG_GREEN,
            "fontWeight": "700",
        },
        {
            "if": {"filter_query": "{status} = 'Non-Compliant'", "column_id": "status"},
            "color": T.RAG_RED,
            "fontWeight": "700",
        },
        {
            "if": {"filter_query": "{approved_patch_count} = 0", "column_id": "approved_patch_count"},
            "color": T.RAG_GREEN,
            "fontWeight": "600",
        },
        {
            "if": {"filter_query": "{approved_patch_count} > 0", "column_id": "approved_patch_count"},
            "color": T.RAG_RED,
            "fontWeight": "600",
        },
        {"if": {"state": "active"}, "backgroundColor": T.BG_CARD_HOVER, "border": f"1px solid {T.BORDER}"},
    ]

    server_table = dash_table.DataTable(
        id="server-compliance-inventory-table",
        columns=_SERVER_COMPLIANCE_COLUMNS,
        data=server_rows,
        sort_action="native",
        sort_mode="multi",
        filter_action="native",
        filter_options={"case": "insensitive", "placeholder_text": "🔍 Filter..."},
        page_size=10,
        style_table={"overflowX": "auto"},
        style_header={
            "backgroundColor": T.BG_PRIMARY,
            "color": T.TEXT_SECONDARY,
            "fontWeight": "600",
            "fontSize": "0.75rem",
            "textTransform": "uppercase",
            "letterSpacing": "0.06em",
            "border": f"1px solid {T.BORDER}",
        },
        style_cell={
            "backgroundColor": T.BG_CARD,
            "color": T.TEXT_PRIMARY,
            "border": f"1px solid {T.BORDER}",
            "fontSize": "0.85rem",
            "padding": "8px 12px",
            "fontFamily": "Inter, -apple-system, sans-serif",
        },
        style_data_conditional=server_style_data_conditional,
        style_filter={
            "backgroundColor": T.BG_CARD_HOVER,
            "color": T.TEXT_PRIMARY,
            "border": f"1px solid {T.BORDER}",
            "fontSize": "0.80rem",
        },
    )

    sla_counts = sla_data.get("sla_counts", {})
    type_counts = sla_data.get("type_counts", {})
    patch_rows = sla_data.get("patch_detail_rows", [])

    aging_fig = charts.patch_sla_aging_bar(sla_counts)
    type_fig = charts.patch_type_donut(type_counts)

    breach_count = sla_data.get("sla_breach_count", 0)
    high_risk_count = sla_data.get("high_risk_count", 0)

    style_data_conditional = [
        # SLA Breach (>90d) - Red
        {
            "if": {"filter_query": "{sla_bucket} = '> 90 Days (SLA Breach)'", "column_id": "sla_bucket"},
            "color": T.RAG_RED,
            "fontWeight": "700",
        },
        # High Risk (31-90d) - Orange
        {
            "if": {"filter_query": "{sla_bucket} = '31 - 90 Days (High Risk)'", "column_id": "sla_bucket"},
            "color": "#FF9800",
            "fontWeight": "600",
        },
        # Warning (8-30d) - Amber
        {
            "if": {"filter_query": "{sla_bucket} = '8 - 30 Days (Warning)'", "column_id": "sla_bucket"},
            "color": T.RAG_AMBER,
        },
        # Within SLA (<7d) - Green
        {
            "if": {"filter_query": "{sla_bucket} = '< 7 Days (Within SLA)'", "column_id": "sla_bucket"},
            "color": T.RAG_GREEN,
        },
        # Severity Critical
        {
            "if": {"filter_query": "{severity} = 'CRITICAL'", "column_id": "severity"},
            "color": T.RAG_RED,
            "fontWeight": "600",
        },
        {"if": {"state": "active"}, "backgroundColor": T.BG_CARD_HOVER, "border": f"1px solid {T.BORDER}"},
    ]

    table = dash_table.DataTable(
        id="patch-sla-inventory-table",
        columns=_PATCH_COLUMNS,
        data=patch_rows,
        sort_action="native",
        sort_mode="multi",
        filter_action="native",
        filter_options={"case": "insensitive", "placeholder_text": "🔍 Filter..."},
        page_size=12,
        style_table={"overflowX": "auto"},
        style_header={
            "backgroundColor": T.BG_PRIMARY,
            "color": T.TEXT_SECONDARY,
            "fontWeight": "600",
            "fontSize": "0.75rem",
            "textTransform": "uppercase",
            "letterSpacing": "0.06em",
            "border": f"1px solid {T.BORDER}",
        },
        style_cell={
            "backgroundColor": T.BG_CARD,
            "color": T.TEXT_PRIMARY,
            "border": f"1px solid {T.BORDER}",
            "fontSize": "0.85rem",
            "padding": "8px 12px",
            "fontFamily": "Inter, -apple-system, sans-serif",
        },
        style_data_conditional=style_data_conditional,
        style_filter={
            "backgroundColor": T.BG_CARD_HOVER,
            "color": T.TEXT_PRIMARY,
            "border": f"1px solid {T.BORDER}",
            "fontSize": "0.80rem",
        },
    )

    return html.Div(
        [
            # Section 1: Server Patch & Software Compliance Ledger
            dbc.Card(
                [
                    dbc.CardHeader(
                        dbc.Row(
                            [
                                dbc.Col(
                                    html.Span([
                                        html.Span("🖥️", style={"marginRight": "8px"}),
                                        html.Span("Server Patch & Software Compliance Ledger", style=T.FONT_SECTION_TITLE),
                                        dbc.Badge(f"{server_total} Servers", color="primary", className="ms-2"),
                                        dbc.Badge(f"✅ Compliant (0 Patches): {server_compliant}", color="success", className="ms-1"),
                                        dbc.Badge(
                                            f"⚠️ Non-Compliant (≥1 Patches): {server_non_compliant}",
                                            color="danger" if server_non_compliant > 0 else "secondary",
                                            className="ms-1",
                                        ),
                                        dbc.Badge(f"{server_pct:.1f}% Compliance", color="info", className="ms-1"),
                                    ]),
                                    md=8,
                                ),
                                dbc.Col(
                                    html.Div(
                                        [
                                            html.Span(
                                                "Rule: 0 Approved Patches = Compliant · ≥1 = Non-Compliant",
                                                style={"fontSize": "0.75rem", "color": T.TEXT_MUTED},
                                            ),
                                        ],
                                        style={"textAlign": "right"},
                                    ),
                                    md=4,
                                ),
                            ],
                            align="center",
                        ),
                        style={"backgroundColor": T.BG_CARD, "borderBottom": f"1px solid {T.BORDER}"},
                    ),
                    dbc.CardBody(server_table),
                ],
                style={"backgroundColor": T.BG_CARD, "border": f"1px solid {T.BORDER}", "borderRadius": "8px", "marginBottom": "20px"},
            ),

            # Section 2: Top Visuals Row
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    html.Span([
                                        html.Span("⏱️", style={"marginRight": "8px"}),
                                        html.Span("Patch SLA Aging & Risk Distribution", style=T.FONT_SECTION_TITLE),
                                        dbc.Badge(f"{breach_count} Breached SLA", color="danger" if breach_count > 0 else "success", className="ms-2"),
                                        dbc.Badge(f"{high_risk_count} High Risk", color="warning", className="ms-1"),
                                    ]),
                                    style={"backgroundColor": T.BG_CARD, "borderBottom": f"1px solid {T.BORDER}"},
                                ),
                                dbc.CardBody(
                                    dcc.Graph(figure=aging_fig, config={"displayModeBar": False}, style={"height": "250px"}),
                                    style={"padding": "10px"},
                                ),
                            ],
                            style={"backgroundColor": T.BG_CARD, "border": f"1px solid {T.BORDER}", "borderRadius": "8px", "height": "100%"},
                        ),
                        md=7,
                        className="mb-3",
                    ),
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    html.Span([
                                        html.Span("📦", style={"marginRight": "8px"}),
                                        html.Span("OS vs 3rd-Party Software Breakdown", style=T.FONT_SECTION_TITLE),
                                    ]),
                                    style={"backgroundColor": T.BG_CARD, "borderBottom": f"1px solid {T.BORDER}"},
                                ),
                                dbc.CardBody(
                                    dcc.Graph(figure=type_fig, config={"displayModeBar": False}, style={"height": "250px"}),
                                    style={"padding": "10px"},
                                ),
                            ],
                            style={"backgroundColor": T.BG_CARD, "border": f"1px solid {T.BORDER}", "borderRadius": "8px", "height": "100%"},
                        ),
                        md=5,
                        className="mb-3",
                    ),
                ],
                className="g-3",
            ),
            # Detailed Patch Grid
            dbc.Card(
                [
                    dbc.CardHeader(
                        dbc.Row(
                            [
                                dbc.Col(
                                    html.Span([
                                        html.Span("📋", style={"marginRight": "8px"}),
                                        html.Span("Fleet Patch Inventory & SLA Aging Ledger", style=T.FONT_SECTION_TITLE),
                                        dbc.Badge(f"{len(patch_rows)} Pending Patches", color="primary", className="ms-2"),
                                    ]),
                                    md=7,
                                ),
                                dbc.Col(
                                    html.Div(
                                        [
                                            html.Span("🔍 Excel-style column filters & sorting enabled below each header",
                                                      style={"fontSize": "0.75rem", "color": T.TEXT_MUTED}),
                                        ],
                                        style={"textAlign": "right"},
                                    ),
                                    md=5,
                                ),
                            ],
                            align="center",
                        ),
                        style={"backgroundColor": T.BG_CARD, "borderBottom": f"1px solid {T.BORDER}"},
                    ),
                    dbc.CardBody(table),
                ],
                style={"backgroundColor": T.BG_CARD, "border": f"1px solid {T.BORDER}", "borderRadius": "8px", "marginBottom": "20px"},
            ),
        ]
    )
