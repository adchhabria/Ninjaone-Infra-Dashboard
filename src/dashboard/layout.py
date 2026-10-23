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


def build_header(
    last_refreshed: datetime | None = None,
    active_filter_label: str = "Global Overview",
    is_live: bool = False,
    base_url: str = "",
    theme_mode: str = "dark",
) -> html.Div:
    """Top navigation bar with brand, active filter badge, auth controls, theme toggle, settings, and refresh buttons."""
    p = T.get_theme_palette(theme_mode)
    ts = (last_refreshed or datetime.now(timezone.utc)).strftime("%Y-%m-%d %H:%M:%S UTC")
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
                                dcc.Loading(
                                    html.Span(
                                        f"Last updated: {ts}",
                                        id="last-updated-text",
                                        style={
                                            "fontSize": "0.75rem", "color": p["text_muted"],
                                            "marginRight": "14px", "lineHeight": "34px",
                                        },
                                    ),
                                    type="dot",
                                    color=T.ACCENT_CYAN,
                                    style={"display": "inline-block", "marginRight": "14px"},
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
                                    style={"fontSize": "0.8rem"},
                                ),
                                dbc.Button(
                                    "☀️ Light" if theme_mode == "dark" else "🌙 Dark",
                                    id="theme-toggle-btn",
                                    color="secondary",
                                    outline=True,
                                    size="sm",
                                    className="me-2",
                                    style={"fontSize": "0.8rem"},
                                ),
                                dbc.Button(
                                    "🚀 Update Available",
                                    id="header-update-badge-btn",
                                    color="warning",
                                    size="sm",
                                    className="me-2",
                                    style={"fontSize": "0.8rem", "fontWeight": "600", "display": "none"},
                                ),
                                dbc.Button(
                                    "⚙️ Settings",
                                    id="open-settings-btn",
                                    color="dark",
                                    outline=True,
                                    size="sm",
                                    className="me-2",
                                    style={"fontSize": "0.8rem", "borderColor": p["border"]},
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
        id="dashboard-header",
        style={
            "backgroundColor": p["bg_card"],
            "borderBottom": f"1px solid {p['border']}",
            "padding": "10px 0",
            "marginBottom": "16px",
            "position": "sticky",
            "top": "0",
            "zIndex": "1000",
        },
    )


CUSTOM_CSS = """
@keyframes expandDonutCard {
    0% {
        opacity: 0.6;
        transform: scale(0.97);
    }
    100% {
        opacity: 1;
        transform: scale(1);
    }
}
.os-donut-col-expanded {
    animation: expandDonutCard 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    transition: all 0.4s ease-in-out;
}
.os-donut-col {
    transition: all 0.4s ease-in-out;
}

/* Light Theme Styling */
.theme-light {
    background-color: #F8FAFC !important;
    color: #0F172A !important;
}
.theme-light h1, .theme-light h2, .theme-light h3, .theme-light h4, .theme-light h5, .theme-light h6 {
    color: #0F172A !important;
}
.theme-light .card, .theme-light .card-header, .theme-light .card-body {
    background-color: #FFFFFF !important;
    border-color: #E2E8F0 !important;
    color: #0F172A !important;
}
.theme-light .card p,
.theme-light .card span:not(.badge),
.theme-light .card label {
    color: #0F172A;
}
.theme-light .text-muted, .theme-light .text-secondary {
    color: #475569 !important;
}
/* Ensure white/near-white inline colors flip to dark slate in light mode */
.theme-light [style*="#E6EDF3"],
.theme-light [style*="#e6edf3"],
.theme-light [style*="#FFFFFF"]:not(.badge):not(.btn-primary):not(.btn-success):not(.btn-danger):not(.btn-info),
.theme-light [style*="#ffffff"]:not(.badge):not(.btn-primary):not(.btn-success):not(.btn-danger):not(.btn-info),
.theme-light [style*="rgb(230, 237, 243)"],
.theme-light [style*="rgb(255, 255, 255)"]:not(.badge):not(.btn-primary):not(.btn-success):not(.btn-danger):not(.btn-info) {
    color: #0F172A !important;
}
.theme-light [style*="#161B22"],
.theme-light [style*="#161b22"],
.theme-light [style*="#0D1117"],
.theme-light [style*="#0d1117"] {
    background-color: #FFFFFF !important;
    border-color: #E2E8F0 !important;
}
.theme-light #dashboard-header {
    background-color: #FFFFFF !important;
    border-bottom: 1px solid #E2E8F0 !important;
}
.theme-light .card {
    background-color: #FFFFFF !important;
    border-color: #E2E8F0 !important;
    color: #0F172A !important;
}
.theme-light .card-header {
    background-color: #FFFFFF !important;
    border-bottom-color: #E2E8F0 !important;
    color: #0F172A !important;
}
.theme-light .card-body {
    background-color: #FFFFFF !important;
    color: #0F172A !important;
}
.theme-light .table {
    color: #0F172A !important;
    border-color: #E2E8F0 !important;
}
.theme-light .table th {
    background-color: #F1F5F9 !important;
    color: #0F172A !important;
    border-color: #E2E8F0 !important;
}
.theme-light .table td {
    background-color: #FFFFFF !important;
    color: #0F172A !important;
    border-color: #E2E8F0 !important;
}
.theme-light .nav-pills .nav-link:not(.active) {
    color: #475569 !important;
}
.theme-light .nav-pills .nav-link.active {
    background-color: #2F81F7 !important;
    color: #FFFFFF !important;
}
.theme-light .filter-dd .Select-control {
    background-color: #FFFFFF !important;
    color: #0F172A !important;
    border: 1px solid #CBD5E1 !important;
}
.theme-light .filter-dd .Select-menu-outer {
    background-color: #FFFFFF !important;
    color: #0F172A !important;
    border: 1px solid #CBD5E1 !important;
}
.theme-light .filter-dd .Select-value-label {
    color: #0F172A !important;
}
.theme-light .filter-dd .Select-placeholder {
    color: #64748B !important;
}
.theme-light .filter-dd .Select-option {
    background-color: #FFFFFF !important;
    color: #0F172A !important;
}
.theme-light .filter-dd .Select-option.is-focused {
    background-color: #F1F5F9 !important;
}
.theme-light #last-updated-text {
    color: #64748B !important;
}
.theme-light .dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner th {
    background-color: #F1F5F9 !important;
    color: #0F172A !important;
}
.theme-light .dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner td {
    background-color: #FFFFFF !important;
    color: #0F172A !important;
}
.theme-light .dash-table-container input.dash-filter--case--sensitive,
.theme-light .dash-table-container input.dash-filter--case--insensitive {
    background-color: #F8FAFC !important;
    color: #0F172A !important;
}

/* Settings Modal & All Modals Light Theme */
.theme-light.settings-modal .modal-content,
.theme-light .settings-modal .modal-content,
.theme-light .modal-content {
    background-color: #FFFFFF !important;
    color: #0F172A !important;
    border: 1px solid #E2E8F0 !important;
}
.theme-light.settings-modal .modal-header,
.theme-light .settings-modal .modal-header,
.theme-light .modal-header,
.theme-light .settings-modal-header {
    background-color: #FFFFFF !important;
    border-bottom: 1px solid #E2E8F0 !important;
    color: #0F172A !important;
}
.theme-light.settings-modal .modal-title,
.theme-light .settings-modal .modal-title,
.theme-light .modal-title {
    color: #0F172A !important;
}
.theme-light.settings-modal .modal-body,
.theme-light .settings-modal .modal-body,
.theme-light .modal-body,
.theme-light .settings-modal-body {
    background-color: #FFFFFF !important;
    color: #0F172A !important;
}
.theme-light.settings-modal .modal-footer,
.theme-light .settings-modal .modal-footer,
.theme-light .modal-footer,
.theme-light .settings-modal-footer {
    background-color: #F8FAFC !important;
    border-top: 1px solid #E2E8F0 !important;
    color: #0F172A !important;
}

/* Modal Tabs in Light Theme */
.theme-light.settings-modal .nav-tabs,
.theme-light .settings-modal .nav-tabs,
.theme-light .modal .nav-tabs {
    border-bottom: 1px solid #CBD5E1 !important;
}
.theme-light.settings-modal .nav-tabs .nav-link,
.theme-light .settings-modal .nav-tabs .nav-link,
.theme-light .modal .nav-tabs .nav-link {
    color: #64748B !important;
    background-color: transparent !important;
    border: 1px solid transparent !important;
}
.theme-light.settings-modal .nav-tabs .nav-link:hover,
.theme-light .settings-modal .nav-tabs .nav-link:hover,
.theme-light .modal .nav-tabs .nav-link:hover {
    color: #0F172A !important;
    border-color: #E2E8F0 #E2E8F0 transparent !important;
}
.theme-light.settings-modal .nav-tabs .nav-link.active,
.theme-light .settings-modal .nav-tabs .nav-link.active,
.theme-light .modal .nav-tabs .nav-link.active {
    color: #2F81F7 !important;
    background-color: #FFFFFF !important;
    border-color: #CBD5E1 #CBD5E1 #FFFFFF !important;
    font-weight: 600 !important;
}

/* Modal Accordions in Light Theme */
.theme-light.settings-modal .accordion-item,
.theme-light .settings-modal .accordion-item,
.theme-light .modal .accordion-item {
    background-color: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    color: #0F172A !important;
}
.theme-light.settings-modal .accordion-button,
.theme-light .settings-modal .accordion-button,
.theme-light .modal .accordion-button {
    background-color: #F8FAFC !important;
    color: #0F172A !important;
    border: none !important;
}
.theme-light.settings-modal .accordion-button:not(.collapsed),
.theme-light .settings-modal .accordion-button:not(.collapsed),
.theme-light .modal .accordion-button:not(.collapsed) {
    background-color: #EFF6FF !important;
    color: #1D4ED8 !important;
    box-shadow: inset 0 -1px 0 #DBEAFE !important;
}
.theme-light.settings-modal .accordion-button::after,
.theme-light .settings-modal .accordion-button::after,
.theme-light .modal .accordion-button::after {
    filter: invert(0) !important;
}
.theme-light.settings-modal .accordion-body,
.theme-light .settings-modal .accordion-body,
.theme-light .modal .accordion-body {
    background-color: #FFFFFF !important;
    color: #0F172A !important;
}

/* Modal Form Controls, Selects, Inputs in Light Theme */
.theme-light.settings-modal .form-control,
.theme-light .settings-modal .form-control,
.theme-light .modal .form-control {
    background-color: #FFFFFF !important;
    color: #0F172A !important;
    border: 1px solid #CBD5E1 !important;
}
.theme-light.settings-modal .form-control:focus,
.theme-light .settings-modal .form-control:focus,
.theme-light .modal .form-control:focus {
    background-color: #FFFFFF !important;
    color: #0F172A !important;
    border-color: #2F81F7 !important;
    box-shadow: 0 0 0 0.2rem rgba(47, 129, 247, 0.25) !important;
}
.theme-light.settings-modal .form-control::placeholder,
.theme-light .settings-modal .form-control::placeholder,
.theme-light .modal .form-control::placeholder {
    color: #94A3B8 !important;
}
.theme-light.settings-modal .form-select,
.theme-light .settings-modal .form-select,
.theme-light .modal .form-select {
    background-color: #FFFFFF !important;
    color: #0F172A !important;
    border: 1px solid #CBD5E1 !important;
}
.theme-light.settings-modal .form-select option,
.theme-light .settings-modal .form-select option,
.theme-light .modal .form-select option {
    background-color: #FFFFFF !important;
    color: #0F172A !important;
}
.theme-light.settings-modal .input-group-text,
.theme-light .settings-modal .input-group-text,
.theme-light .modal .input-group-text {
    background-color: #F1F5F9 !important;
    color: #475569 !important;
    border: 1px solid #CBD5E1 !important;
}
.theme-light.settings-modal .form-check-label,
.theme-light .settings-modal .form-check-label,
.theme-light .modal .form-check-label {
    color: #0F172A !important;
}
.theme-light.settings-modal .form-check-input,
.theme-light .settings-modal .form-check-input,
.theme-light .modal .form-check-input {
    background-color: #FFFFFF !important;
    border: 1px solid #CBD5E1 !important;
}

/* Modal Typography, Labels, Code, and Alerts in Light Theme */
.theme-light.settings-modal label,
.theme-light .settings-modal label,
.theme-light .modal label,
.theme-light.settings-modal .form-label,
.theme-light .settings-modal .form-label {
    color: #334155 !important;
}
.theme-light.settings-modal .modal-body p,
.theme-light .settings-modal .modal-body p,
.theme-light.settings-modal .modal-body span:not(.badge),
.theme-light .settings-modal .modal-body span:not(.badge) {
    color: #475569 !important;
}
.theme-light.settings-modal .modal-body h1,
.theme-light .settings-modal .modal-body h1,
.theme-light.settings-modal .modal-body h2,
.theme-light .settings-modal .modal-body h2,
.theme-light.settings-modal .modal-body h3,
.theme-light .settings-modal .modal-body h3,
.theme-light.settings-modal .modal-body h4,
.theme-light .settings-modal .modal-body h4,
.theme-light.settings-modal .modal-body h5,
.theme-light .settings-modal .modal-body h5,
.theme-light.settings-modal .modal-body h6,
.theme-light .settings-modal .modal-body h6,
.theme-light.settings-modal .modal-body b,
.theme-light .settings-modal .modal-body b,
.theme-light.settings-modal .modal-body strong,
.theme-light .settings-modal .modal-body strong {
    color: #0F172A !important;
}
.theme-light.settings-modal hr,
.theme-light .settings-modal hr,
.theme-light .modal hr {
    border-color: #E2E8F0 !important;
    opacity: 1 !important;
}
.theme-light.settings-modal .alert-info,
.theme-light .settings-modal .alert-info,
.theme-light .modal .alert-info {
    background-color: rgba(47, 129, 247, 0.08) !important;
    border: 1px solid #BFDBFE !important;
    color: #1E3A8A !important;
}
.theme-light.settings-modal .alert-info ol,
.theme-light.settings-modal .alert-info li,
.theme-light .settings-modal .alert-info ol,
.theme-light .settings-modal .alert-info li {
    color: #1E293B !important;
}
.theme-light.settings-modal code,
.theme-light .settings-modal code,
.theme-light .modal code {
    color: #0969DA !important;
    background-color: #EFF6FF !important;
    padding: 2px 6px !important;
    border-radius: 4px !important;
}
.theme-light.settings-modal .card,
.theme-light .settings-modal .card {
    background-color: #F8FAFC !important;
    border-color: #E2E8F0 !important;
}
.theme-light.settings-modal .badge.bg-dark,
.theme-light .settings-modal .badge.bg-dark {
    background-color: #E2E8F0 !important;
    color: #334155 !important;
    border: 1px solid #CBD5E1 !important;
}
.theme-light.settings-modal .btn-close,
.theme-light .settings-modal .btn-close,
.theme-light .modal .btn-close {
    filter: none !important;
}

/* Multi-select Dropdown Pills */
.theme-light .Select--multi .Select-value {
    background-color: #E0E7FF !important;
    border: 1px solid #C7D2FE !important;
    color: #3730A3 !important;
}
.theme-light .Select--multi .Select-value-icon {
    border-right: 1px solid #C7D2FE !important;
    color: #4F46E5 !important;
}
.theme-light .Select--multi .Select-value-icon:hover {
    background-color: #C7D2FE !important;
    color: #1E1B4B !important;
}
.theme-light .Select--multi .Select-value-label {
    color: #3730A3 !important;
}
"""


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
    theme_mode: str = "dark",
) -> html.Div:
    """Renders the inner content for the currently active tab."""
    if active_tab == "tab-executive":
        return html.Div(
            [
                # Row 1: KPI Summary Strip
                dbc.Row(
                    dbc.Col(build_kpi_strip(data, theme_mode=theme_mode), width=12),
                    className="mb-4",
                ),
                # Row 2: OS Landscape (Windows and Linux side by side or single expanded)
                dbc.Row(
                    dbc.Col(build_os_panel(data.os, theme_mode=theme_mode), width=12),
                    className="mb-4",
                ),
                # Row 3: Multi-Cloud Server Hosting
                dbc.Row(
                    dbc.Col(build_server_hosting_panel(data.servers, theme_mode=theme_mode), width=12),
                    className="mb-4",
                ),
                # Row 4: Speedometer Patch Gauge
                dbc.Row(
                    dbc.Col(build_patch_panel(data.patches, red_limit=patch_red, amber_limit=patch_amber, green_target=patch_green, theme_mode=theme_mode), width=12),
                    className="mb-4",
                ),
                # Row 5: EOL Compliance & Risk Analysis
                dbc.Row(
                    dbc.Col(build_eol_panel(data.os, theme_mode=theme_mode), width=12),
                    className="mb-4",
                ),
                # Row 6: Organization Compliance Table
                dbc.Row(
                    dbc.Col(build_compliance_table(data.org_table, theme_mode=theme_mode), width=12),
                    className="mb-4",
                ),
            ]
        )

    elif active_tab == "tab-patch-ops":
        return html.Div(
            [
                dbc.Row(
                    dbc.Col(build_sla_panel(data.sla, data.patches, theme_mode=theme_mode), width=12),
                    className="mb-4",
                ),
            ]
        )

    elif active_tab == "tab-reboots":
        return html.Div(
            [
                dbc.Row(
                    dbc.Col(build_reboot_failures_panel(data.sla, theme_mode=theme_mode), width=12),
                    className="mb-4",
                ),
            ]
        )

    elif active_tab == "tab-reports":
        return html.Div(
            [
                dbc.Row(
                    dbc.Col(build_reports_panel(data, theme_mode=theme_mode), width=12),
                    className="mb-4",
                ),
            ]
        )

    return html.Div("Tab content not found.", style={"color": T.TEXT_MUTED})


def build_body(
    data,
    active_tab: str = "tab-executive",
    eol_days: int = 180,
    patch_red: float = 60.0,
    patch_amber: float = 84.0,
    patch_green: float = 85.0,
    theme_mode: str = "dark",
) -> html.Div:
    """Builds the main container with dropdown filters, map, tab bar, and tab content."""
    org_list = data.org_options or [{"label": o.name, "value": str(o.id)} for o in data.organizations]
    location_opts = data.location_options or list({d.location_name for d in data.devices_raw if d.location_name})
    os_opts = data.os_family_options or ["Windows", "Linux", "macOS"]
    role_opts = getattr(data, "role_options", None) or list({d.device_role for d in data.devices_raw if getattr(d, "device_role", None)})
    region_opts = getattr(data, "region_options", None)

    return html.Div(
        [
            # Multi-Dimensional Dropdown Filter Bar
            dbc.Container(
                dbc.Row(
                    dbc.Col(
                        build_org_slicer(
                            org_list,
                            location_opts,
                            os_opts,
                            role_options=role_opts,
                            active_org_id=data.active_org_id,
                            active_location=data.active_location,
                            active_os_family=data.active_os_family,
                            active_roles=getattr(data, "active_roles", None),
                            active_patch_type=getattr(data, "active_patch_type", "both"),
                            theme_mode=theme_mode,
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
                        build_map_panel(data.map_data, active_region=data.active_region, theme_mode=theme_mode),
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
                        theme_mode=theme_mode,
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

def build_layout(data, theme_mode: str = "dark") -> html.Div:
    """Assemble the full dashboard page from DashboardData."""
    is_live = coordinator.is_live
    base_url = coordinator.base_url
    p = T.get_theme_palette(theme_mode)

    return html.Div(
        [
            # Auto-refresh interval (every 5 minutes)
            dcc.Interval(id="auto-refresh", interval=5 * 60 * 1000, n_intervals=0),

            # State stores
            dcc.Store(id="theme-store", storage_type="local", data=theme_mode),
            dcc.Store(id="last-refresh-store"),
            dcc.Store(id="filter-state-store", data={
                "org_ids": [],
                "region": "Global / All",
                "locations": [],
                "os_families": [],
                "roles": [],
                "patch_type": "both",
            }),
            dcc.Store(id="active-tab-store", data="tab-executive"),
            dcc.Store(id="threshold-settings-store", data={
                "eol_days": int(os.getenv("EOL_THRESHOLD_DAYS", "180")),
                "patch_red": float(os.getenv("PATCH_RED_LIMIT", "60.0")),
                "patch_amber": float(os.getenv("PATCH_AMBER_LIMIT", "84.0")),
                "patch_green": float(os.getenv("PATCH_GREEN_TARGET", "85.0")),
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
                "included_keywords": ["Cumulative Update", "Security Update"],
                "excluded_products": [".NET", "Office", "SQL", "Visual Studio", "Exchange", "SharePoint"],
                "selected_patch_titles": [],
            }),
            dcc.Store(id="auth-state-store", data={
                "is_live": is_live,
                "base_url": base_url,
            }),

            # In-App Settings Modal
            build_settings_modal(theme_mode=theme_mode),

            # Auto-Update Periodic Checker & Notification Modal
            dcc.Interval(id="auto-update-check-interval", interval=60 * 60 * 1000, n_intervals=0),
            dcc.Interval(id="update-progress-interval", interval=500, n_intervals=0, disabled=True),
            dcc.Store(id="auto-update-info-store"),
            dbc.Modal(
                [
                    dbc.ModalHeader(
                        dbc.ModalTitle("🚀 New Toolkit Version Available!"),
                        close_button=True,
                        style={"backgroundColor": p["bg_card"], "borderBottom": f"1px solid {p['border']}"},
                    ),
                    dbc.ModalBody(
                        [
                            html.Div(id="update-prompt-content"),
                            html.Div(id="update-prompt-status", className="mt-3"),
                        ],
                        style={"backgroundColor": p["bg_primary"], "color": p["text_primary"], "padding": "20px"},
                    ),
                    dbc.ModalFooter(
                        [
                            dbc.Button(
                                "Remind Me Later",
                                id="update-prompt-dismiss-btn",
                                color="secondary",
                                outline=True,
                                size="sm",
                                className="me-auto",
                            ),
                            dbc.Button(
                                "🚀 Update & Restart Now",
                                id="update-prompt-confirm-btn",
                                color="success",
                                size="sm",
                                style={"fontWeight": "600"},
                            ),
                        ],
                        style={"backgroundColor": p["bg_card"], "borderTop": f"1px solid {p['border']}"},
                    ),
                ],
                id="update-prompt-modal",
                is_open=False,
                centered=True,
                size="lg",
            ),

            # Persistent Browser Download Components
            dcc.Download(id="download-excel-data"),
            dcc.Download(id="download-pdf-data"),
            dcc.Download(id="download-html-data"),

            # Header
            build_header(data.fetched_at, data.active_filter_label, is_live=is_live, base_url=base_url, theme_mode=theme_mode),

            # Main content container
            html.Div(build_body(data, active_tab="tab-executive", theme_mode=theme_mode), id="dashboard-body"),
        ],
        id="dashboard-theme-wrapper",
        className=f"theme-{theme_mode}",
        style={"backgroundColor": p["bg_primary"], "minHeight": "100vh", "color": p["text_primary"], "transition": "background-color 0.3s ease, color 0.3s ease"},
    )
