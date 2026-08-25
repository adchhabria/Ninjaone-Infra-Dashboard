"""
Executive Excel & PDF Report Generation Hub.

Provides single-click multi-sheet Excel workbook (.xlsx) downloads
and executive PDF audit report (.pdf) downloads matching active slicers.
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
            # Hidden download trigger components for in-browser file delivery
            dcc.Download(id="download-excel-data"),
            dcc.Download(id="download-pdf-data"),

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
                                        html.Span("Executive PDF Audit Report (.pdf)", style=T.FONT_SECTION_TITLE),
                                        dbc.Badge("Direct PDF", color="primary", className="ms-2"),
                                    ]),
                                    style={"backgroundColor": T.BG_CARD, "borderBottom": f"1px solid {T.BORDER}"},
                                ),
                                dbc.CardBody(
                                    [
                                        html.P(
                                            "Generates a multi-page, publication-grade executive audit document with styled tables, KPI cards, and SLA breakdown matching your active filters:",
                                            style=T.FONT_BODY,
                                        ),
                                        html.Ul(
                                            [
                                                html.Li([html.Strong("Executive KPI Matrix: "), "Overall RAG score, device health, fleet patch coverage."]),
                                                html.Li([html.Strong("Patch SLA Aging: "), "Granular breakdown of within-SLA, warning, and breached patches."]),
                                                html.Li([html.Strong("Multi-Cloud Hosting: "), "AWS, Azure, GCP, VMs, and physical server inventory."]),
                                                html.Li([html.Strong("EOL Audit Ledger: "), "Complete list of past-support operating systems with days overdue."]),
                                                html.Li([html.Strong("Client Scorecards: "), "Organization-by-organization compliance status."]),
                                            ],
                                            style={**T.FONT_BODY, "fontSize": "0.85rem", "marginBottom": "20px"},
                                        ),
                                        html.Div(
                                            [
                                                html.Span("Active Scope: ", style={"fontWeight": "600", "color": T.TEXT_SECONDARY}),
                                                html.Span(data.active_filter_label, style={"color": T.ACCENT_CYAN, "fontWeight": "700"}),
                                            ],
                                            style={"marginBottom": "15px", "fontSize": "0.9rem"},
                                        ),
                                        dbc.Button(
                                            "📄 Generate & Download PDF Report (.pdf)",
                                            id="btn-generate-pdf-trigger",
                                            color="primary",
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
