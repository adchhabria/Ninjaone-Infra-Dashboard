"""
Executive Excel & PDF Report Generation Hub.

Inspired by ninjaone-patch-toolkit:
Provides single-click multi-sheet Excel workbook (.xlsx) downloads
and executive PDF presentations.
"""

from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import dcc, html

from src.dashboard import theme as T
from src.metrics.aggregator import DashboardData


def build_reports_panel(data: DashboardData) -> html.Div:
    """
    Renders the report export hub with Excel and PDF download triggers.
    """
    return html.Div(
        [
            # Hidden download trigger component
            dcc.Download(id="download-excel-data"),

            dbc.Row(
                [
                    # Card 1: Multi-Sheet Excel Export
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    html.Span([
                                        html.Span("📊", style={"marginRight": "8px"}),
                                        html.Span("Multi-Sheet Excel Audit Workbook (.xlsx)", style=T.FONT_SECTION_TITLE),
                                        dbc.Badge("Interactive", color="success", className="ms-2"),
                                    ]),
                                    style={"backgroundColor": T.BG_CARD, "borderBottom": f"1px solid {T.BORDER}"},
                                ),
                                dbc.CardBody(
                                    [
                                        html.P(
                                            "Exports a complete enterprise workbook with formatted headers, auto-filters, and 6 specialized worksheets matching the current filter scope:",
                                            style=T.FONT_BODY,
                                        ),
                                        html.Ul(
                                            [
                                                html.Li([html.Strong("Executive Summary: "), "High-level metrics, compliance score, RAG status."]),
                                                html.Li([html.Strong("Organization Compliance: "), "Org-by-org device counts, patch %, OS %, and scores."]),
                                                html.Li([html.Strong("EOL Device Ledger: "), "Expired & approaching EOL hardware with days overdue."]),
                                                html.Li([html.Strong("Patch SLA Aging: "), "Granular patch inventory categorized by SLA aging bracket."]),
                                                html.Li([html.Strong("Needs Reboot: "), "Watchlist of endpoints requiring restart."]),
                                                html.Li([html.Strong("Patch Failures: "), "Failed updates with diagnostic error codes."]),
                                            ],
                                            style={**T.FONT_BODY, "fontSize": "0.85rem", "marginBottom": "20px"},
                                        ),
                                        dbc.Button(
                                            "📥 Download Excel Audit (.xlsx)",
                                            id="btn-download-excel",
                                            color="success",
                                            size="lg",
                                            className="w-100",
                                            style={"fontWeight": "600"},
                                        ),
                                    ],
                                    style={"padding": "20px"},
                                ),
                            ],
                            style={"backgroundColor": T.BG_CARD, "border": f"1px solid {T.BORDER}", "borderRadius": "8px", "height": "100%"},
                        ),
                        md=6,
                        className="mb-3",
                    ),

                    # Card 2: Executive PDF Presentation
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    html.Span([
                                        html.Span("📄", style={"marginRight": "8px"}),
                                        html.Span("Executive PDF & Image Presentation", style=T.FONT_SECTION_TITLE),
                                        dbc.Badge("PDF / PNG", color="primary", className="ms-2"),
                                    ]),
                                    style={"backgroundColor": T.BG_CARD, "borderBottom": f"1px solid {T.BORDER}"},
                                ),
                                dbc.CardBody(
                                    [
                                        html.P(
                                            "Export a pixel-perfect, C-level executive compliance presentation in PDF or PNG format via Playwright headless rendering engine.",
                                            style=T.FONT_BODY,
                                        ),
                                        html.Div(
                                            [
                                                html.Span("Active Scope: ", style={"fontWeight": "600", "color": T.TEXT_SECONDARY}),
                                                html.Span(data.active_filter_label, style={"color": T.ACCENT_CYAN, "fontWeight": "700"}),
                                            ],
                                            style={"marginBottom": "15px", "fontSize": "0.9rem"},
                                        ),
                                        html.P(
                                            "To generate a PDF report via CLI at any time:",
                                            style={"fontSize": "0.80rem", "color": T.TEXT_MUTED, "marginBottom": "6px"},
                                        ),
                                        html.Pre(
                                            "python scripts/export_pdf.py --format pdf\npython scripts/export_pdf.py --format png",
                                            style={
                                                "backgroundColor": T.BG_PRIMARY,
                                                "color": T.TEXT_PRIMARY,
                                                "padding": "10px",
                                                "borderRadius": "6px",
                                                "fontSize": "0.80rem",
                                                "border": f"1px solid {T.BORDER}",
                                                "marginBottom": "20px",
                                            },
                                        ),
                                        dbc.Button(
                                            "📄 Generate PDF Report",
                                            id="btn-generate-pdf-trigger",
                                            color="primary",
                                            outline=True,
                                            size="lg",
                                            className="w-100",
                                            style={"fontWeight": "600"},
                                        ),
                                        html.Div(id="pdf-generation-status", style={"marginTop": "10px"}),
                                    ],
                                    style={"padding": "20px"},
                                ),
                            ],
                            style={"backgroundColor": T.BG_CARD, "border": f"1px solid {T.BORDER}", "borderRadius": "8px", "height": "100%"},
                        ),
                        md=6,
                        className="mb-3",
                    ),
                ],
                className="g-3",
            ),
        ]
    )
