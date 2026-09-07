"""
Dashboard layout — full responsive page structure with multi-tab navigation.

Assembles:
- Header with Authentication status badge, Sign In/Sign Out buttons, Settings modal & Live status
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
from src.dashboard.components.server_panel import build_server_hosting_panel
from src.dashboard.components.patch_panel import build_patch_panel
from src.dashboard.components.eol_panel import build_eol_panel
from src.dashboard.components.compliance_table import build_compliance_table
from src.dashboard.components.sla_panel import build_sla_panel
from src.dashboard.components.reboot_failures_panel import build_reboot_failures_panel
from src.dashboard.components.reports_panel import build_reports_panel
from src.dashboard.components.settings_modal import build_settings_modal
from src.metrics.data_provider import coordinator


def build_header(last_refreshed: datetime | None = None, active_filter_label: str = "Global Overview", is_live: bool = False, base_url: str = "") -> html.Div:
    """Top navigation bar with brand, active filter badge, auth controls, settings, and refresh buttons."""
    ts = (last_refreshed or datetime.now(timezone.utc)).strftime("%Y-%m-%d %H:%M UTC")
    clean_url = (base_url or "app.ninjarmm.com").replace("https://", "").replace("http://", "").rstrip("/")

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
                                # Persistent Auth Controls
                                html.Div(
                                    [
                                        dbc.Badge(
                                            f"🟢 Live: {clean_url}",
                                            id="header-live-badge",
                                            color="success",
                                            className="me-2",
                                            style={"fontSize": "0.78rem", "padding": "5px 10px", "display": "inline-block" if is_live else "none"},
                                        ),
                                        dbc.Button(
                                            "🚪 Sign Out",
                                            id="header-signout-btn",
                                            color="danger",
                                            outline=True,
                                            size="sm",
                                            className="me-2",
                                            style={"fontSize": "0.8rem", "display": "inline-block" if is_live else "none"},
                                        ),
                                        dbc.Badge(
                                            "🟡 Demo Mode",
                                            id="header-demo-badge",
                                            color="warning",
                                            className="me-2",
                                            style={"fontSize": "0.78rem", "padding": "5px 10px", "display": "none" if is_live else "inline-block"},
                                        ),
                                        dbc.Button(
                                            "🔐 Sign In to NinjaOne",
                                            id="header-signin-btn",
                                            color="primary",
                                            size="sm",
                                            className="me-2",
                                            style={"fontSize": "0.8rem", "fontWeight": "600", "display": "none" if is_live else "inline-block"},
                                        ),
                                    ],
                                    id="header-auth-container",
                                    style={"display": "inline-flex", "alignItems": "center"},
                                ),
                                dbc.Button(
                                    "📤 Share Report",
                                    id="header-share-btn",
                                    color="success",
                                    outline=True,
                                    size="sm",
                                    className="me-2",
                                    href="/download/html",
                                    external_link=True,
                                    style={"fontSize": "0.8rem"},
                                ),
                                dbc.Button(
                                    "📄 PDF",
                                    id="header-pdf-btn",
                                    color="primary",
                                    outline=True,
                                    size="sm",
                                    className="me-2",
                                    href="/download/pdf",
                                    external_link=True,
                                    style={"fontSize": "0.8rem"},
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


# ---------------------------------------------------------------------------
# Tab Routing
# ---------------------------------------------------------------------------

def build_tab_content(
    data,
    active_tab: str = "tab-executive",
    eol_days: int = 180,
    patch_red: float = 60.0,
    patch_amber: float = 84.0,
    patch_green: float = 85.0,
) -> html.Div:
    """Renders the inner content for the currently active tab."""
    if active_tab == "tab-executive":
        return html.Div(
            [
                # Row 1: KPI Summary Strip
                dbc.Row(
                    dbc.Col(build_kpi_strip(data), width=12),
                    className="mb-4",
                ),
                # Row 2: OS Landscape (Windows and Linux side by side)
                dbc.Row(
                    dbc.Col(build_os_panel(data.os), width=12),
                    className="mb-4",
                ),
                # Row 3: Multi-Cloud Server Hosting
                dbc.Row(
                    dbc.Col(build_server_hosting_panel(data.servers), width=12),
                    className="mb-4",
                ),
                # Row 4: Speedometer Patch Gauge
                dbc.Row(
                    dbc.Col(build_patch_panel(data.patches, red_limit=patch_red, amber_limit=patch_amber, green_target=patch_green), width=12),
                    className="mb-4",
                ),
                # Row 5: EOL Compliance & Risk Analysis
                dbc.Row(
                    dbc.Col(build_eol_panel(data.os), width=12),
                    className="mb-4",
                ),
                # Row 6: Organization Compliance Table
                dbc.Row(
                    dbc.Col(build_compliance_table(data.org_table), width=12),
                    className="mb-4",
                ),
            ]
        )

    elif active_tab == "tab-patch-ops":
        return html.Div(
            [
                dbc.Row(
                    dbc.Col(build_sla_panel(data.sla, data.patches), width=12),
                    className="mb-4",
                ),
            ]
        )

    elif active_tab == "tab-reboots":
        return html.Div(
            [
                dbc.Row(
                    dbc.Col(build_reboot_failures_panel(data.sla), width=12),
                    className="mb-4",
                ),
            ]
        )

    elif active_tab == "tab-reports":
        return html.Div(
            [
                dbc.Row(
                    dbc.Col(build_reports_panel(data), width=12),
                    className="mb-4",
                ),
            ]
        )

    return html.Div("Tab content not found.", style={"color": T.TEXT_MUTED})


def build_body(data, active_tab: str = "tab-executive", eol_days: int = 180, patch_red: float = 60.0, patch_amber: float = 84.0, patch_green: float = 85.0) -> html.Div:
    """Builds the main container with slicers, map, tab bar, and tab content."""
    org_list = data.org_options or [{"label": o.name, "value": str(o.id)} for o in data.organizations]
    location_opts = data.location_options or list({d.location_name for d in data.devices_raw if d.location_name})
    os_opts = data.os_family_options or ["Windows", "Linux", "macOS"]

    return html.Div(
        [
            # Multi-Dimensional Slicer Bar
            dbc.Container(
                dbc.Row(
                    dbc.Col(
                        build_org_slicer(
                            org_list,
                            location_opts,
                            os_opts,
                            active_org_id=data.active_org_id,
                            active_location=data.active_location,
                            active_os_family=data.active_os_family,
                        ),
                        width=12,
                    ),
                    className="mb-3",
                ),
                fluid=True,
            ),

            # Geographic Map Panel
            dbc.Container(
                dbc.Row(
                    dbc.Col(
                        build_map_panel(data.map_data, active_region=data.active_region),
                        width=12,
                    ),
                    className="mb-4",
                ),
                fluid=True,
            ),

            # Multi-Tab Navigation Bar
            dbc.Container(
                dbc.Row(
                    dbc.Col(
                        dbc.Nav(
                            [
                                dbc.NavLink(
                                    [html.Span("📊", style={"marginRight": "6px"}), "Executive Overview"],
                                    id="nav-tab-executive",
                                    active=(active_tab == "tab-executive"),
                                    href="#",
                                    className="me-2",
                                    style={"fontWeight": "600", "cursor": "pointer"},
                                ),
                                dbc.NavLink(
                                    [html.Span("⏱️", style={"marginRight": "6px"}), "Patch Operations & SLA Aging"],
                                    id="nav-tab-patch-ops",
                                    active=(active_tab == "tab-patch-ops"),
                                    href="#",
                                    className="me-2",
                                    style={"fontWeight": "600", "cursor": "pointer"},
                                ),
                                dbc.NavLink(
                                    [html.Span("🔄", style={"marginRight": "6px"}), "Reboots & Failure Watchlist"],
                                    id="nav-tab-reboots",
                                    active=(active_tab == "tab-reboots"),
                                    href="#",
                                    className="me-2",
                                    style={"fontWeight": "600", "cursor": "pointer"},
                                ),
                                dbc.NavLink(
                                    [html.Span("📥", style={"marginRight": "6px"}), "Reports & Excel Export"],
                                    id="nav-tab-reports",
                                    active=(active_tab == "tab-reports"),
                                    href="#",
                                    style={"fontWeight": "600", "cursor": "pointer"},
                                ),
                            ],
                            pills=True,
                            className="mb-3",
                        ),
                        width=12,
                    )
                ),
                fluid=True,
            ),

            # Tab Content Area
            dbc.Container(
                html.Div(
                    build_tab_content(
                        data,
                        active_tab=active_tab,
                        eol_days=eol_days,
                        patch_red=patch_red,
                        patch_amber=patch_amber,
                        patch_green=patch_green,
                    ),
                    id="tab-content-container",
                ),
                fluid=True,
            ),
        ]
    )


# ---------------------------------------------------------------------------
# Master Page Layout
# ---------------------------------------------------------------------------

def build_layout(data) -> html.Div:
    """Assemble the full dashboard page from DashboardData."""
    is_live = coordinator.is_live
    base_url = coordinator.base_url

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
                "server_patch_threshold": 0,
                "custom_eol_dates": {
                    "Windows Server 2008": "01/14/2020",
                    "Windows Server 2012": "10/10/2023",
                    "Windows Server 2016": "01/12/2027",
                    "Windows Server 2019": "01/09/2029",
                    "Windows Server 2022": "10/14/2031",
                    "Windows Server 2025": "10/10/2034",
                    "Ubuntu": "04/30/2025",
                    "RHEL": "06/30/2024",
                    "CentOS": "06/30/2024",
                    "Debian": "06/30/2026",
                },
            }),
            dcc.Store(id="auth-state-store", data={
                "is_live": is_live,
                "base_url": base_url,
            }),

            # In-App Settings Modal
            build_settings_modal(),

            # Persistent Browser Download Components
            dcc.Download(id="download-excel-data"),
            dcc.Download(id="download-pdf-data"),
            dcc.Download(id="download-html-data"),

            # Header
            build_header(data.fetched_at, data.active_filter_label, is_live=is_live, base_url=base_url),

            # Main content container
            html.Div(build_body(data, active_tab="tab-executive"), id="dashboard-body"),
        ],
        style={"backgroundColor": T.BG_PRIMARY, "minHeight": "100vh", "color": T.TEXT_PRIMARY},
    )
