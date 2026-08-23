"""
Dedicated End-of-Life (EOL) Compliance & Audit Panel.

Features:
- EOL Status Distribution Donut (Supported vs Approaching vs Expired)
- At-Risk OS Version Breakdown Bar Chart
- Full Interactive EOL Audit DataTable with Excel-style column filters, Days Overdue and Risk Ratings
"""

from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import dash_table, dcc, html

from src.dashboard import charts, theme as T


_EOL_COLUMNS = [
    {"name": "Device Name", "id": "name", "type": "text"},
    {"name": "Organization", "id": "org_name", "type": "text"},
    {"name": "Region", "id": "region", "type": "text"},
    {"name": "OS Build", "id": "os", "type": "text"},
    {"name": "EOL Date", "id": "eol_date", "type": "text"},
    {"name": "Days Overdue", "id": "days_overdue", "type": "numeric"},
    {"name": "Status", "id": "status", "type": "text"},
    {"name": "Risk Level", "id": "risk_level", "type": "text"},
]


def build_eol_panel(os_data: dict) -> dbc.Card:
    """
    Renders dedicated EOL graphs and full audit DataTable with Excel filtering.
    """
    status_counts = os_data.get("eol_status_counts", {})
    eol_by_os = os_data.get("eol_by_os", {})
    eol_table_data = os_data.get("eol_table_data", [])

    status_fig = charts.eol_status_donut(status_counts)
    by_os_fig = charts.eol_by_os_bar(eol_by_os)

    eol_count = os_data.get("eol_count", 0)
    approaching_count = os_data.get("approaching_count", 0)
    badge_color = "danger" if eol_count > 0 else "warning" if approaching_count > 0 else "success"

    style_data_conditional = [
        # Expired (EOL) / Critical rows
        {
            "if": {"filter_query": "{risk_level} = 'CRITICAL'", "column_id": "risk_level"},
            "color": T.RAG_RED,
            "fontWeight": "700",
        },
        {
            "if": {"filter_query": "{risk_level} = 'HIGH'", "column_id": "risk_level"},
            "color": T.RAG_RED,
            "fontWeight": "600",
        },
        {
            "if": {"filter_query": "{risk_level} = 'MEDIUM'", "column_id": "risk_level"},
            "color": T.RAG_AMBER,
            "fontWeight": "600",
        },
        {
            "if": {"filter_query": "{days_overdue} > 0", "column_id": "days_overdue"},
            "color": T.RAG_RED,
            "fontWeight": "600",
        },
        {
            "if": {"filter_query": "{status} = 'Expired (EOL)'", "column_id": "status"},
            "color": T.RAG_RED,
        },
        {
            "if": {"filter_query": "{status} = 'Approaching EOL'", "column_id": "status"},
            "color": T.RAG_AMBER,
        },
        {"if": {"state": "active"}, "backgroundColor": T.BG_CARD_HOVER, "border": f"1px solid {T.BORDER}"},
    ]

    table = dash_table.DataTable(
        id="eol-audit-table",
        columns=_EOL_COLUMNS,
        data=eol_table_data,
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
            "padding": "7px 12px",
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

    return dbc.Card(
        [
            dbc.CardHeader(
                dbc.Row(
                    [
                        dbc.Col(
                            html.Span([
                                html.Span("⚠️", style={"marginRight": "8px"}),
                                html.Span("Operating System End-of-Life (EOL) & Lifecycle Audit", style=T.FONT_SECTION_TITLE),
                                dbc.Badge(f"{eol_count} Expired (Non-Compliant)", color=badge_color, className="ms-2"),
                                dbc.Badge(f"{approaching_count} Approaching EOL (<180d)", color="warning", className="ms-1"),
                            ]),
                            md=7,
                        ),
                        dbc.Col(
                            html.Div(
                                html.Span("🔍 Excel-style column filters & sorting enabled below each header",
                                          style={"fontSize": "0.75rem", "color": T.TEXT_MUTED}),
                                style={"textAlign": "right"},
                            ),
                            md=5,
                        ),
                    ],
                    align="center",
                ),
                style={"backgroundColor": T.BG_CARD, "borderBottom": f"1px solid {T.BORDER}"},
            ),
            dbc.CardBody(
                [
                    # Top Row: 2 EOL Visuals
                    dbc.Row(
                        [
                            dbc.Col(dcc.Graph(figure=status_fig, config={"displayModeBar": False}, style={"height": "240px"}), md=5),
                            dbc.Col(dcc.Graph(figure=by_os_fig, config={"displayModeBar": False}, style={"height": "240px"}), md=7),
                        ],
                        className="mb-3 g-3",
                    ),
                    html.Hr(style={"borderColor": T.BORDER}),
                    html.Div(
                        [
                            html.Span(
                                "📋 Detailed EOL Device Inventory & Risk Ledger",
                                style={**T.FONT_SECTION_TITLE, "color": T.ACCENT_ORANGE, "marginBottom": "10px", "display": "block"},
                            ),
                            table,
                        ]
                    ),
                ]
            ),
        ],
        style={"backgroundColor": T.BG_CARD, "border": f"1px solid {T.BORDER}", "borderRadius": "8px", "marginBottom": "20px"},
    )
