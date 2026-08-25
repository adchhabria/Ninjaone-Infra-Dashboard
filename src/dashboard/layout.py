"""
Dashboard layout — full responsive page structure with multi-tab navigation.

Assembles:
- Header with Settings modal & Live status
- Excel-style Multi-Dimensional Slicer Bar (Organization, Location, OS Family)
- Interactive World Map with Region Filters (hover-only tooltips)
- Multi-Tab Navigation:
    1. 📊 Executive Overview (Separated OS Donuts, Server Compliance & Multi-Cloud Server Hosting)
    2. ⏱️ Patch Operations & SLA Aging
    3. 🔄 Reboots & Failure Watchlist
    4. 📥 Reports & Excel Export
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Optional

import dash_bootstrap_components as dbc
from dash import dcc, html

from src.dashboard import theme as T
from src.dashboard.components.org_slicer import build_org_slicer
from src.dashboard.components.map_panel import build_map_panel
from src.dashboard.components.kpi_cards import build_kpi_strip
from src.dashboard.components.os_panel import build_os_panel
from src.dashboard.components.server_panel import (
    build_server_compliance_panel,
    build_server_hosting_panel,
)
from src.dashboard.components.patch_panel import build_patch_panel
from src.dashboard.components.eol_panel import build_eol_panel
from src.dashboard.components.compliance_table import build_compliance_table
from src.dashboard.components.sla_panel import build_sla_panel
from src.dashboard.components.reboot_failures_panel import build_reboot_failures_panel
from src.dashboard.components.reports_panel import build_reports_panel
from src.dashboard.components.settings_modal import build_settings_modal


def build_header(last_refreshed: datetime | None = None, active_filter_label: str = "Global Overview") -> html.Div:
    """Top navigation bar with brand, active filter badge, settings, and refresh buttons."""
    ts = (last_refreshed or datetime.now(timezone.utc)).strftime("%Y-%m-%d %H:%M UTC")
    return html.Div(
        dbc.Container(
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            [
                                html.Span("⚡", style={"fontSize": "1.6rem", "marginRight": "10px"}),
                                html.Span("Ninjaone Infra Dashboard", style={
                                    "fontSize": "1.30rem", "fontWeight": "700", "color": T.ACCENT_BLUE,
                                }),
                                dbc.Badge(
                                    active_filter_label,
                                    id="header-filter-badge",
                                    color="info",
                                    className="ms-3",
                                    style={"fontSize": "0.78rem", "padding": "5px 10px", "borderRadius": "12px"},
                                ),
                            ],
                            style={"display": "flex", "alignItems": "center"},
                        ),
                        width="auto",
                    ),
                    dbc.Col(
                        html.Div(
                            [
                                html.Span(
                                    f"Last updated: {ts}",
                                    id="last-updated-text",
                                    style={
                                        "fontSize": "0.75rem", "color": T.TEXT_MUTED,
                                        "marginRight": "14px", "lineHeight": "34px",
                                    },
                                ),
                                dbc.Button(
                                    "⚙️ Settings",
                                    id="open-settings-btn",
                                    color="dark",
                                    outline=True,
                                    size="sm",
                                    className="me-2",
                                    style={"fontSize": "0.8rem", "borderColor": T.BORDER},
                                ),
                                dbc.Button(
                                    "↻ Refresh Data",
                                    id="refresh-btn",
                                    color="primary",
                                    outline=True,
                                    size="sm",
                                    style={"fontSize": "0.8rem"},
                                ),
                            ],
                            style={"display": "flex", "alignItems": "center", "justifyContent": "flex-end"},
                        ),
                        style={"textAlign": "right"},
                    ),
                ],
                align="center",
            ),
            fluid=True,
        ),
        style={
            "backgroundColor": T.BG_CARD,
            "borderBottom": f"1px solid {T.BORDER}",
            "padding": "10px 0",
            "marginBottom": "16px",
            "position": "sticky",
            "top": "0",
            "zIndex": "1000",
        },
    )


def build_tab_content(data, active_tab: str = "tab-executive", threshold_settings: dict | None = None) -> html.Div:
    """Renders the content for the currently active navigation tab."""
    ts = threshold_settings or {
        "eol_days": 180,
        "patch_red": 60.0,
        "patch_amber": 84.0,
        "patch_green": 85.0,
    }

    if active_tab == "tab-patch-ops":
        return build_sla_panel(data.sla)
    elif active_tab == "tab-reboots":
        return build_reboot_failures_panel(data.sla)
    elif active_tab == "tab-reports":
        return build_reports_panel(data)

    # Default: Executive Overview
    return html.Div(
        [
            # 1. Executive KPI Strip
            build_kpi_strip(data),

            # 2. OS Landscape (2 Separate Donuts) + Server Compliance Panel (Roles & Online %)
            dbc.Row(
                [
                    dbc.Col(build_os_panel(data.os), md=6, className="mb-3"),
                    dbc.Col(build_server_compliance_panel(data.servers), md=6, className="mb-3"),
                ],
                className="g-3",
            ),

            # 3. Separated Server Hosting Infrastructure Panel (AWS, Azure, GCP, VMs, Physical Donut)
            dbc.Row(
                dbc.Col(build_server_hosting_panel(data.servers), md=12, className="mb-3"),
            ),

            # 4. Patch Compliance Speedometer Gauge (Configurable Thresholds)
            dbc.Row(
                dbc.Col(
                    build_patch_panel(
                        data.patches,
                        red_limit=ts.get("patch_red", 60.0),
                        amber_limit=ts.get("patch_amber", 84.0),
                        green_target=ts.get("patch_green", 85.0),
                    ),
                    md=12,
                    className="mb-3",
                ),
            ),

            # 5. Dedicated End-of-Life (EOL) Analytics & Audit DataTable
            dbc.Row(
                dbc.Col(build_eol_panel(data.os), md=12, className="mb-3"),
            ),

            # 6. Organization Compliance DataTable
            dbc.Row(
                dbc.Col(build_compliance_table(data.org_table), md=12, className="mb-4"),
            ),
        ]
    )


def build_body(data, active_tab: str = "tab-executive", threshold_settings: dict | None = None) -> list:
    """Build all content panels from DashboardData."""
    return [
        dbc.Container(
            [
                # Common Section 1: Excel-style Multi-Dimensional Slicer Bar
                build_org_slicer(
                    org_options=data.org_options,
                    location_options=data.location_options,
                    os_family_options=data.os_family_options,
                    active_org_id=data.active_org_id,
                    active_location=data.active_location,
                    active_os_family=data.active_os_family,
                ),

                # Common Section 2: World Map & Regional Slicer
                build_map_panel(data.map_data, data.active_region),

                # Section 3: Navigation Tabs
                dbc.Tabs(
                    [
                        dbc.Tab(label="📊 Executive Overview", tab_id="tab-executive", label_style={"fontWeight": "600"}),
                        dbc.Tab(label="⏱️ Patch Operations & SLA Aging", tab_id="tab-patch-ops", label_style={"fontWeight": "600"}),
                        dbc.Tab(label="🔄 Reboots & Failure Watchlist", tab_id="tab-reboots", label_style={"fontWeight": "600"}),
                        dbc.Tab(label="📥 Reports & Excel Export", tab_id="tab-reports", label_style={"fontWeight": "600"}),
                    ],
                    id="dashboard-tabs",
                    active_tab=active_tab,
                    className="mb-3",
                ),

                # Section 4: Dynamic Tab Content Container
                html.Div(build_tab_content(data, active_tab=active_tab, threshold_settings=threshold_settings), id="tab-content-container"),

                # Footer
                html.Div(
                    [
                        html.Hr(style={"borderColor": T.BORDER}),
                        html.Div(
                            f"NinjaOne Unified Compliance & Patch Operations Toolkit · "
                            f"Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d')} · Dual Management & Operational Engine",
                            style={"textAlign": "center", "color": T.TEXT_MUTED,
                                   "fontSize": "0.75rem", "paddingBottom": "24px"},
                        ),
                    ]
                ),
            ],
            fluid=True,
        )
    ]


def build_layout(data) -> html.Div:
    """Assemble the full dashboard page from DashboardData."""
    return html.Div(
        [
            # Auto-refresh interval (every 5 minutes)
            dcc.Interval(id="auto-refresh", interval=5 * 60 * 1000, n_intervals=0),

            # State stores
            dcc.Store(id="last-refresh-store"),
            dcc.Store(id="filter-state-store", data={
                "org_id": None,
                "region": "Global / All",
                "location": "All Locations",
                "os_family": "All OS Families",
            }),
            dcc.Store(id="active-tab-store", data="tab-executive"),
            dcc.Store(id="threshold-settings-store", data={
                "eol_days": int(os.getenv("EOL_THRESHOLD_DAYS", "180")),
                "patch_red": float(os.getenv("PATCH_RED_LIMIT", "60.0")),
                "patch_amber": float(os.getenv("PATCH_AMBER_LIMIT", "84.0")),
                "patch_green": float(os.getenv("PATCH_GREEN_TARGET", "85.0")),
            }),

            # In-App Settings Modal
            build_settings_modal(),

            # Header
            build_header(data.fetched_at, data.active_filter_label),

            # Main content container
            html.Div(build_body(data, active_tab="tab-executive"), id="dashboard-body"),
        ],
        style={"backgroundColor": T.BG_PRIMARY, "minHeight": "100vh", "color": T.TEXT_PRIMARY},
    )
