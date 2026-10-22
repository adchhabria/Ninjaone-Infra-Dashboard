"""Per-organization compliance table with Excel-style header filtering and RAG status indicators."""

from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import dash_table, html

from src.dashboard import theme as T


_RAG_ICON = {"GREEN": "🟢", "AMBER": "🟡", "RED": "🔴"}

_COLUMNS = [
    {"name": "Organization", "id": "org_name", "type": "text"},
    {"name": "Location", "id": "region", "type": "text"},
    {"name": "Devices", "id": "device_count", "type": "numeric"},
    {"name": "Online %", "id": "online_pct", "type": "numeric", "format": {"specifier": ".1f"}},
    {"name": "Patch %", "id": "patch_pct", "type": "numeric", "format": {"specifier": ".1f"}},
    {"name": "OS %", "id": "os_pct", "type": "numeric", "format": {"specifier": ".1f"}},
    {"name": "EOL Devices", "id": "eol_count", "type": "numeric"},
    {"name": "Compliance Score", "id": "compliance_score", "type": "numeric", "format": {"specifier": ".1f"}},
    {"name": "Status", "id": "rag_icon", "type": "text"},
]


def build_compliance_table(org_table: list[dict], theme_mode: str = "dark") -> dbc.Card:
    p = T.get_theme_palette(theme_mode)
    # Add RAG icon column
    rows = []
    for row in org_table:
        r = dict(row)
        r["rag_icon"] = _RAG_ICON.get(r.get("rag", "RED"), "🔴")
        rows.append(r)

    style_data_conditional = [
        # Red rows
        {
            "if": {"filter_query": "{rag_icon} = '🔴'", "column_id": "compliance_score"},
            "color": T.RAG_RED, "fontWeight": "700",
        },
        # Amber rows
        {
            "if": {"filter_query": "{rag_icon} = '🟡'", "column_id": "compliance_score"},
            "color": T.RAG_AMBER, "fontWeight": "700",
        },
        # Green rows
        {
            "if": {"filter_query": "{rag_icon} = '🟢'", "column_id": "compliance_score"},
            "color": T.RAG_GREEN, "fontWeight": "700",
        },
        # Patch % column — color-code low values
        {
            "if": {"filter_query": "{patch_pct} < 60", "column_id": "patch_pct"},
            "color": T.RAG_RED,
        },
        {
            "if": {
                "filter_query": "{patch_pct} >= 60 && {patch_pct} < 85",
                "column_id": "patch_pct",
            },
            "color": T.RAG_AMBER,
        },
        # Row hover
        {"if": {"state": "active"}, "backgroundColor": p["bg_card_hover"], "border": f"1px solid {p['border']}"},
    ]

    table = dash_table.DataTable(
        id="org-compliance-table",
        columns=_COLUMNS,
        data=rows,
        sort_action="native",
        sort_mode="multi",
        filter_action="native",
        filter_options={"case": "insensitive", "placeholder_text": "🔍 Filter..."},
        page_size=15,
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
            "fontSize": "0.875rem",
            "padding": "8px 12px",
            "fontFamily": "Inter, -apple-system, sans-serif",
        },
        style_data_conditional=style_data_conditional,
        style_filter={
            "backgroundColor": p["bg_card_hover"],
            "color": p["text_primary"],
            "border": f"1px solid {p['border']}",
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
                                html.Span("📊", style={"marginRight": "8px"}),
                                html.Span("Organization Compliance Ledger", style={**T.FONT_SECTION_TITLE, "color": p["text_primary"]}),
                                dbc.Badge(f"{len(rows)} Organizations", color="secondary", className="ms-2"),
                            ]),
                            md=7,
                        ),
                        dbc.Col(
                            html.Div(
                                html.Span("🔍 Excel-style column filters & sorting enabled below each header",
                                          style={"fontSize": "0.75rem", "color": p["text_muted"]}),
                                style={"textAlign": "right"},
                            ),
                            md=5,
                        ),
                    ],
                    align="center",
                ),
                style={"backgroundColor": p["bg_card"], "borderBottom": f"1px solid {p['border']}"},
            ),
            dbc.CardBody(table, style={"backgroundColor": p["bg_card"]}),
        ],
        style={"backgroundColor": p["bg_card"], "border": f"1px solid {p['border']}", "borderRadius": "8px", "marginBottom": "20px"},
    )
