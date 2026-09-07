"""
Executive Excel, PDF & Standalone HTML Report Generation Hub.

Provides single-click multi-sheet Excel workbook (.xlsx),
executive PDF audit report (.pdf), and standalone interactive HTML report (.html)
downloads matching active slicers.
"""

from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import html

from src.dashboard import theme as T
from src.metrics.aggregator import DashboardData


def build_reports_panel(data: DashboardData) -> html.Div:
    """
    Renders the report export hub with Excel, PDF, and HTML download triggers.
    """
    return html.Div(
        [
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
                                            href="/download/excel",
                                            external_link=True,
                                            style={"fontWeight": "600"},
                                        ),
                                    ],
                                    style={"padding": "20px"},
                                ),
                            ],
                            style={"backgroundColor": T.BG_CARD, "border": f"1px solid {T.BORDER}", "borderRadius": "8px", "height": "100%"},
                        ),
                        md=4,
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
                                        dbc.Button(
                                            "📄 Generate & Download PDF (.pdf)",
                                            id="btn-generate-pdf-trigger",
                                            color="primary",
                                            size="lg",
                                            className="w-100",
                                            href="/download/pdf",
                                            external_link=True,
                                            style={"fontWeight": "600"},
                                        ),
                                    ],
                                    style={"padding": "20px"},
                                ),
                            ],
                            style={"backgroundColor": T.BG_CARD, "border": f"1px solid {T.BORDER}", "borderRadius": "8px", "height": "100%"},
                        ),
                        md=4,
                        className="mb-3",
                    ),

                    # Card 3: Standalone Shareable Interactive HTML Report
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    html.Span([
                                        html.Span("📤", style={"marginRight": "8px"}),
                                        html.Span("Standalone Interactive HTML (.html)", style=T.FONT_SECTION_TITLE),
                                        dbc.Badge("Shareable", color="info", className="ms-2"),
                                    ]),
                                    style={"backgroundColor": T.BG_CARD, "borderBottom": f"1px solid {T.BORDER}"},
                                ),
                                dbc.CardBody(
                                    [
                                        html.P(
                                            "Generates a standalone, self-contained HTML executive dashboard that can be emailed or shared directly with stakeholders. Opens in any browser:",
                                            style=T.FONT_BODY,
                                        ),
                                        html.Ul(
                                            [
                                                html.Li([html.Strong("Zero Installation: "), "Opens instantly in Chrome, Edge, Safari, Firefox."]),
                                                html.Li([html.Strong("Live Interactive Charts: "), "Embedded Plotly charts with zoom and hover tooltips."]),
                                                html.Li([html.Strong("Full Audit Tables: "), "Complete client scorecards, EOL hardware & reboot lists."]),
                                                html.Li([html.Strong("Offline Ready: "), "Does not require a running server or login credentials."]),
                                                html.Li([html.Strong("Filtered Scope: "), f"Exported for {data.active_filter_label}."]),
                                            ],
                                            style={**T.FONT_BODY, "fontSize": "0.85rem", "marginBottom": "20px"},
                                        ),
                                        dbc.Button(
                                            "📤 Export & Share HTML Report (.html)",
                                            id="btn-download-html-trigger",
                                            color="info",
                                            size="lg",
                                            className="w-100",
                                            href="/download/html",
                                            external_link=True,
                                            style={"fontWeight": "600"},
                                        ),
                                    ],
                                    style={"padding": "20px"},
                                ),
                            ],
                            style={"backgroundColor": T.BG_CARD, "border": f"1px solid {T.BORDER}", "borderRadius": "8px", "height": "100%"},
                        ),
                        md=4,
                        className="mb-3",
                    ),
                ],
                className="g-3",
            ),
        ]
    )
