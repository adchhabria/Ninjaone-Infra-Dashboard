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
from src.dashboard.components.reports_panel import build_reports_panel
from src.dashboard.components.settings_modal import build_settings_modal
from src.metrics.data_provider import coordinator


def build_header(
    last_refreshed: datetime | None = None,
    active_filter_label: str = "Global Overview",
    is_live: bool = False,
    base_url: str = "",
    theme_mode: str = "light",
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

/* Light Theme Core */
.theme-light {
    background-color: #F8FAFC !important;
    color: #0F172A !important;
}
.theme-light h1, .theme-light h2, .theme-light h3, .theme-light h4, .theme-light h5, .theme-light h6 {
    color: #0F172A !important;
}
.theme-light p,
.theme-light span:not(.badge),
.theme-light label,
.theme-light li,
.theme-light strong,
.theme-light b {
    color: #0F172A;
}
.theme-light .text-muted, 
.theme-light .text-secondary {
    color: #334155 !important;
}

/* Force ALL inline dark backgrounds (both hex and rgb formats) to crisp light mode */
.theme-light [style*="#161B22"],
.theme-light [style*="#161b22"],
.theme-light [style*="#0D1117"],
.theme-light [style*="#0d1117"],
.theme-light [style*="#1C2128"],
.theme-light [style*="#1c2128"],
.theme-light [style*="rgb(22, 27, 34)"],
.theme-light [style*="rgb(13, 17, 23)"],
.theme-light [style*="rgb(28, 33, 40)"] {
    background-color: #FFFFFF !important;
    border-color: #CBD5E1 !important;
}

/* Force ALL inline light/white/grey text colors (both hex and rgb formats) to dark high-contrast slate */
.theme-light [style*="#E6EDF3"],
.theme-light [style*="#e6edf3"],
.theme-light [style*="rgb(230, 237, 243)"],
.theme-light [style*="#FFFFFF"]:not(.badge):not(.btn),
.theme-light [style*="#ffffff"]:not(.badge):not(.btn),
.theme-light [style*="rgb(255, 255, 255)"]:not(.badge):not(.btn) {
    color: #0F172A !important;
}

.theme-light [style*="#8B949E"],
.theme-light [style*="#8b949e"],
.theme-light [style*="rgb(139, 148, 158)"],
.theme-light [style*="#484F58"],
.theme-light [style*="#484f58"],
.theme-light [style*="rgb(72, 79, 88)"] {
    color: #334155 !important;
}

.theme-light [style*="#30363D"],
.theme-light [style*="#30363d"],
.theme-light [style*="rgb(48, 54, 61)"] {
    border-color: #CBD5E1 !important;
}

/* Header & Navigation */
.theme-light #dashboard-header {
    background-color: #FFFFFF !important;
    border-bottom: 1px solid #CBD5E1 !important;
    color: #0F172A !important;
}
.theme-light #dashboard-header h4,
.theme-light #dashboard-header span:not(.badge) {
    color: #0F172A !important;
}
.theme-light #last-updated-text {
    color: #475569 !important;
}

/* Cards & Panels Across All Tabs */
.theme-light .card {
    background-color: #FFFFFF !important;
    border: 1px solid #CBD5E1 !important;
    color: #0F172A !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
}
.theme-light .card-header {
    background-color: #FFFFFF !important;
    border-bottom: 1px solid #CBD5E1 !important;
    color: #0F172A !important;
}
.theme-light .card-header span:not(.badge),
.theme-light .card-header h5,
.theme-light .card-header h6 {
    color: #0F172A !important;
    font-weight: 600 !important;
}
.theme-light .card-body {
    background-color: #FFFFFF !important;
    color: #0F172A !important;
}
.theme-light .card p,
.theme-light .card span:not(.badge),
.theme-light .card label {
    color: #0F172A;
}

/* Nav Pills (Main Dashboard Tab Bar) */
.theme-light .nav-pills .nav-link:not(.active) {
    background-color: #FFFFFF !important;
    color: #334155 !important;
    border: 1px solid #CBD5E1 !important;
}
.theme-light .nav-pills .nav-link:not(.active):hover {
    background-color: #F1F5F9 !important;
    color: #0F172A !important;
}
.theme-light .nav-pills .nav-link.active {
    background-color: #2F81F7 !important;
    color: #FFFFFF !important;
    border-color: #2F81F7 !important;
    box-shadow: 0 2px 4px rgba(47, 129, 247, 0.25) !important;
}

/* Multi-Dimensional Filter Bar & Dropdowns (Dynamic Single-Row Sizing & Non-overlapping Right-Aligned Arrow) */
.filter-bar-card .card-body {
    padding: 8px 14px !important;
}
.filter-dd .Select-control {
    position: relative !important;
    min-height: 34px !important;
    height: 34px !important;
    max-height: 34px !important;
    display: flex !important;
    flex-wrap: nowrap !important;
    align-items: center !important;
    white-space: nowrap !important;
    padding-right: 32px !important;
    box-sizing: border-box !important;
    overflow: visible !important;
}
.filter-dd .Select-multi-value-wrapper {
    display: flex !important;
    align-items: center !important;
    flex: 1 1 auto !important;
    min-width: 0 !important;
    max-width: calc(100% - 2px) !important;
    height: 100% !important;
    overflow-x: auto !important;
    overflow-y: hidden !important;
    white-space: nowrap !important;
    scrollbar-width: none !important;
    -ms-overflow-style: none !important;
}
.filter-dd .Select-multi-value-wrapper::-webkit-scrollbar {
    display: none !important;
}
.filter-dd .Select-placeholder,
.filter-dd.Select--single > .Select-control .Select-value,
.filter-dd .Select--single > .Select-control .Select-value {
    position: relative !important;
    top: auto !important;
    left: auto !important;
    right: auto !important;
    bottom: auto !important;
    line-height: 32px !important;
    font-size: 0.78rem !important;
    padding-left: 8px !important;
    padding-right: 4px !important;
    max-width: 100% !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    white-space: nowrap !important;
    pointer-events: none !important;
    flex: 1 1 auto !important;
}
.filter-dd .Select-input {
    height: 32px !important;
    line-height: 32px !important;
    display: inline-block !important;
    flex: 0 0 auto !important;
}
.filter-dd .Select-input > input {
    padding: 0 !important;
    line-height: 32px !important;
}
.filter-dd .Select-value {
    max-width: 130px !important;
    text-overflow: ellipsis !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    font-size: 0.74rem !important;
    line-height: 1.3 !important;
    margin: 1px 2px !important;
    flex-shrink: 0 !important;
    display: inline-flex !important;
    align-items: center !important;
}
.filter-dd .Select-arrow-zone {
    position: absolute !important;
    right: 8px !important;
    top: 0 !important;
    bottom: 0 !important;
    width: 20px !important;
    margin: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    cursor: pointer !important;
    pointer-events: auto !important;
    z-index: 5 !important;
}
.filter-dd .Select-clear-zone {
    position: absolute !important;
    right: 28px !important;
    top: 0 !important;
    bottom: 0 !important;
    width: 16px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    cursor: pointer !important;
    z-index: 5 !important;
}
.filter-dd .Select-arrow {
    border-color: #8B949E transparent transparent !important;
    border-style: solid !important;
    border-width: 5px 4px 0 4px !important;
    display: inline-block !important;
    height: 0 !important;
    width: 0 !important;
    position: relative !important;
}
.filter-dd .Select-arrow-zone:hover > .Select-arrow {
    border-top-color: #94A3B8 !important;
}

/* Dark Mode Filter Dropdown & Text Styling (Soft slate text, reduced contrast glare) */
.filter-dd .Select-control {
    background-color: #161B22 !important;
    border: 1px solid #30363D !important;
    color: #94A3B8 !important;
}
.filter-dd .Select-control:hover {
    border-color: #484F58 !important;
}
.filter-dd .Select-placeholder {
    color: #64748B !important;
}
.filter-dd .Select-input input {
    color: #94A3B8 !important;
}
.filter-dd .Select-value {
    background-color: #1E293B !important;
    border: 1px solid #334155 !important;
    color: #94A3B8 !important;
}
.filter-dd .Select-value-label {
    color: #94A3B8 !important;
    font-weight: 500 !important;
}
.filter-dd .Select-value-icon {
    border-right: 1px solid #334155 !important;
    color: #64748B !important;
}
.filter-dd .Select-value-icon:hover {
    background-color: rgba(239, 68, 68, 0.2) !important;
    color: #F87171 !important;
}
.filter-dd .Select-menu-outer {
    background-color: #161B22 !important;
    border: 1px solid #30363D !important;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4) !important;
}
.filter-dd .Select-option {
    background-color: #161B22 !important;
    color: #94A3B8 !important;
}
.filter-dd .Select-option.is-focused {
    background-color: #21262D !important;
    color: #CBD5E1 !important;
}
.filter-dd .Select-option.is-selected {
    background-color: #1E293B !important;
    color: #38BDF8 !important;
    font-weight: 600 !important;
}
.Select--multi .Select-value {
    background-color: #1E293B !important;
    border: 1px solid #334155 !important;
    color: #94A3B8 !important;
}
.Select--multi .Select-value-label {
    color: #94A3B8 !important;
}

.theme-light .filter-dd .Select-arrow {
    border-color: #475569 transparent transparent !important;
}
.theme-light .filter-dd .Select-arrow-zone:hover > .Select-arrow {
    border-top-color: #0F172A !important;
}
.filter-dd.is-open > .Select-control .Select-arrow {
    border-color: transparent transparent #8B949E !important;
    border-width: 0 4px 5px 4px !important;
}
.theme-light .filter-dd.is-open > .Select-control .Select-arrow {
    border-color: transparent transparent #475569 !important;
    border-width: 0 4px 5px 4px !important;
}
.theme-light .filter-dd .Select-control {
    background-color: #FFFFFF !important;
    color: #0F172A !important;
    border: 1px solid #CBD5E1 !important;
}
.theme-light .filter-dd .Select-control:hover {
    border-color: #94A3B8 !important;
}
.theme-light .filter-dd .Select-menu-outer {
    background-color: #FFFFFF !important;
    color: #0F172A !important;
    border: 1px solid #CBD5E1 !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important;
}
.theme-light .filter-dd .Select-value {
    background-color: #E0E7FF !important;
    border: 1px solid #C7D2FE !important;
    color: #3730A3 !important;
}
.theme-light .filter-dd .Select-value-label {
    color: #3730A3 !important;
    font-weight: 500 !important;
}
.theme-light .filter-dd .Select-value-icon {
    border-right: 1px solid #C7D2FE !important;
    color: #4F46E5 !important;
}
.theme-light .filter-dd .Select-value-icon:hover {
    background-color: #C7D2FE !important;
    color: #1E1B4B !important;
}
.theme-light .filter-dd .Select-placeholder {
    color: #64748B !important;
}
.theme-light .filter-dd .Select-input input {
    color: #0F172A !important;
}
.theme-light .filter-dd .Select-option {
    background-color: #FFFFFF !important;
    color: #0F172A !important;
}
.theme-light .filter-dd .Select-option.is-focused {
    background-color: #F1F5F9 !important;
    color: #0F172A !important;
}
.theme-light .filter-dd .Select-option.is-selected {
    background-color: #EFF6FF !important;
    color: #1D4ED8 !important;
    font-weight: 600 !important;
}
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

/* DataTables Across All Tabs (Compliance, SLA, Reboots, Failures) */
.theme-light .table {
    color: #0F172A !important;
    border-color: #CBD5E1 !important;
}
.theme-light .table th {
    background-color: #F1F5F9 !important;
    color: #0F172A !important;
    border-color: #CBD5E1 !important;
}
.theme-light .table td {
    background-color: #FFFFFF !important;
    color: #0F172A !important;
    border-color: #E2E8F0 !important;
}
.theme-light .dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner th {
    background-color: #F1F5F9 !important;
    color: #0F172A !important;
    border: 1px solid #CBD5E1 !important;
    font-weight: 600 !important;
}
.theme-light .dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner td {
    background-color: #FFFFFF !important;
    color: #0F172A !important;
    border: 1px solid #E2E8F0 !important;
}
.theme-light .dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner tr:hover td {
    background-color: #F8FAFC !important;
}
.theme-light .dash-table-container input.dash-filter--case--sensitive,
.theme-light .dash-table-container input.dash-filter--case--insensitive {
    background-color: #F8FAFC !important;
    color: #0F172A !important;
    border: 1px solid #CBD5E1 !important;
}

/* Plotly Charts & SVGs (Prevents Dark Boxes and Invisible Text) */
.theme-light .js-plotly-plot .plotly .main-svg:first-child,
.theme-light .js-plotly-plot .plotly .main-svg:first-child > rect.bg,
.theme-light .js-plotly-plot .plotly rect.bg,
.theme-light .js-plotly-plot .plotly rect.plotbg {
    fill: #FFFFFF !important;
    fill-opacity: 1 !important;
}
.theme-light .js-plotly-plot .plotly text.gtitle,
.theme-light .js-plotly-plot .plotly .g-title text {
    fill: #0F172A !important;
    font-weight: 600 !important;
}
.theme-light .js-plotly-plot .plotly .legend text.legendtext {
    fill: #334155 !important;
}
.theme-light .js-plotly-plot .plotly .legend rect.bg {
    fill: #FFFFFF !important;
    stroke: #CBD5E1 !important;
    fill-opacity: 0.95 !important;
}
.theme-light .js-plotly-plot .plotly .xtick text,
.theme-light .js-plotly-plot .plotly .ytick text,
.theme-light .js-plotly-plot .plotly .axis-title text {
    fill: #334155 !important;
}
.theme-light .js-plotly-plot .plotly text.annotation-text {
    fill: #334155 !important;
}
.theme-light .js-plotly-plot .plotly .pie text {
    fill: #0F172A !important;
}
.theme-light .js-plotly-plot .plotly .bar text {
    fill: #0F172A !important;
}
.theme-light .js-plotly-plot .plotly path.domain {
    stroke: #CBD5E1 !important;
}
.theme-light .js-plotly-plot .plotly path.xgrid,
.theme-light .js-plotly-plot .plotly path.ygrid,
.theme-light .js-plotly-plot .plotly path.zeroline {
    stroke: #E2E8F0 !important;
}

/* Settings Modal & All Modals Light Theme */
.theme-light.settings-modal .modal-content,
.theme-light .settings-modal .modal-content,
.theme-light .modal-content {
    background-color: #FFFFFF !important;
    color: #0F172A !important;
    border: 1px solid #CBD5E1 !important;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1) !important;
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
    font-weight: 700 !important;
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

/* Modal Tabs (Settings Modal All Tabs) */
.theme-light.settings-modal .nav-tabs,
.theme-light .settings-modal .nav-tabs,
.theme-light .modal .nav-tabs {
    border-bottom: 1px solid #CBD5E1 !important;
}
.theme-light.settings-modal .nav-tabs .nav-link,
.theme-light .settings-modal .nav-tabs .nav-link,
.theme-light .modal .nav-tabs .nav-link {
    color: #475569 !important;
    background-color: transparent !important;
    border: 1px solid transparent !important;
}
.theme-light.settings-modal .nav-tabs .nav-link:hover,
.theme-light .settings-modal .nav-tabs .nav-link:hover,
.theme-light .modal .nav-tabs .nav-link:hover {
    color: #0F172A !important;
    border-color: #CBD5E1 #CBD5E1 transparent !important;
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
    font-weight: 600 !important;
}
.theme-light.settings-modal .accordion-button:not(.collapsed),
.theme-light .settings-modal .accordion-button:not(.collapsed),
.theme-light .modal .accordion-button:not(.collapsed) {
    background-color: #EFF6FF !important;
    color: #1D4ED8 !important;
    box-shadow: inset 0 -1px 0 #DBEAFE !important;
    font-weight: 600 !important;
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
    color: #334155 !important;
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
    color: #0F172A !important;
    font-weight: 600 !important;
}
.theme-light.settings-modal .modal-body p,
.theme-light .settings-modal .modal-body p,
.theme-light.settings-modal .modal-body span:not(.badge),
.theme-light .settings-modal .modal-body span:not(.badge) {
    color: #334155 !important;
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
    border: 1px solid #CBD5E1 !important;
    color: #0F172A !important;
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
"""


# ---------------------------------------------------------------------------
# Tab Routing
# ---------------------------------------------------------------------------

def build_tab_content(
    data,
    active_tab: str = "tab-executive",
    eol_days: int = 180,
    patch_red: float = 60.0,
    patch_amber: float = 90.0,
    green_target: float = 90.0,
    patch_green: float = 90.0,
    theme_mode: str = "light",
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
                # Row 2: OS Landscape & Patch Category Breakdown
                dbc.Row(
                    dbc.Col(
                        build_os_panel(
                            data.os,
                            type_counts=getattr(data, "sla", {}).get("type_counts", {}),
                            theme_mode=theme_mode,
                        ),
                        width=12,
                    ),
                    className="mb-4",
                ),
                # Row 3: Multi-Cloud Server Hosting
                dbc.Row(
                    dbc.Col(build_server_hosting_panel(data.servers, theme_mode=theme_mode), width=12),
                    className="mb-4",
                ),
                # Row 4: Speedometer Patch Gauge & Year-to-Date (YTD) Trend Line Chart
                dbc.Row(
                    dbc.Col(
                        build_patch_panel(
                            data.patches,
                            red_limit=patch_red,
                            amber_limit=patch_amber,
                            green_target=patch_green,
                            theme_mode=theme_mode,
                            ytd_trend_data=getattr(data, "ytd_trend", None),
                        ),
                        width=12,
                    ),
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
    patch_amber: float = 90.0,
    green_target: float = 90.0,
    patch_green: float = 90.0,
    theme_mode: str = "light",
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
                                    [html.Span("⏱️", style={"marginRight": "6px"}), "Patch Operations Details"],
                                    id="nav-tab-patch-ops",
                                    active=(active_tab == "tab-patch-ops"),
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

def build_layout(data, theme_mode: str = "light") -> html.Div:
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
                "patch_amber": float(os.getenv("PATCH_AMBER_LIMIT", "90.0")),
                "patch_green": float(os.getenv("PATCH_GREEN_TARGET", "90.0")),
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
            dcc.Store(id="dismissed-update-version-store", storage_type="local"),
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
                style={"borderRadius": "16px"},
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
