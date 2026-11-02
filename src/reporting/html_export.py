"""
Standalone Executive HTML Dashboard Generator for NinjaOne Infrastructure & Compliance Dashboard.

Generates a fully self-contained, publication-grade interactive HTML dashboard containing:
  1. Tab 1: Executive Overview (KPIs, OS Landscape & Patch Category Breakdown, Hosting Breakdown
     with interactive toggle, Geographic Distribution World Map, Speedometer Gauge, and YTD Trend Line)
  2. Tab 2: Patch Operations Details (Top 10 Servers with Max Pending Patches, Top 10 Patches Pending
     on Max Servers, and Patch Deployment Failure Triage Ledger)
  3. Interactive Controls: Pure client-side Tab Navigation, Light/Dark Theme Switcher,
     instant Table Search, and Print/PDF export.

Can be shared directly with stakeholders (email, Microsoft Teams, OneDrive, SharePoint)
and opened in any web browser without needing Python, a local server, or NinjaOne credentials.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import plotly.io as pio

from src.dashboard import charts
from src.metrics.aggregator import DashboardData


def generate_html_report(
    data: DashboardData,
    title: str = "NinjaOne Infrastructure & Compliance Executive Dashboard",
    patch_red: float | None = None,
    patch_amber: float | None = None,
    patch_green: float | None = None,
    custom_ytd_trend: dict | None = None,
    theme_mode: str = "light",
) -> str:
    """
    Builds a standalone, responsive executive HTML dashboard matching active dashboard slicers,
    active theme (light or dark), and dynamic compliance thresholds.
    """
    theme_mode = (theme_mode or "light").lower()
    is_light = theme_mode == "light"
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Resolve dynamic compliance thresholds
    red_limit = float(patch_red if patch_red is not None else getattr(data, "patch_red", 60.0))
    amber_limit = float(patch_amber if patch_amber is not None else getattr(data, "patch_amber", 90.0))
    green_target = float(patch_green if patch_green is not None else getattr(data, "patch_green", 90.0))

    # 1. OS & Software Breakdown Donuts
    win_fig = charts.windows_os_donut(data.os.get("windows_version_counts", {}), theme_mode=theme_mode)
    win_chart_html = pio.to_html(win_fig, full_html=False, include_plotlyjs=False, config={"displayModeBar": False, "responsive": True})

    lin_fig = charts.linux_os_donut(data.os.get("linux_version_counts", {}), theme_mode=theme_mode)
    lin_chart_html = pio.to_html(lin_fig, full_html=False, include_plotlyjs=False, config={"displayModeBar": False, "responsive": True})

    type_counts = data.sla.get("type_counts", {})
    type_fig = charts.patch_type_donut(type_counts, theme_mode=theme_mode)
    type_chart_html = pio.to_html(type_fig, full_html=False, include_plotlyjs=False, config={"displayModeBar": False, "responsive": True})

    # 2. Infrastructure Hosting Views (Donut, Org Stacked Bar, Role Heatmap)
    host_donut_fig = charts.hosting_donut(data.servers.get("hosting_counts", {}), theme_mode=theme_mode)
    host_donut_html = pio.to_html(host_donut_fig, full_html=False, include_plotlyjs=False, config={"displayModeBar": False, "responsive": True})

    host_stacked_fig = charts.hosting_org_stacked_bar(data.servers.get("org_distribution", []), theme_mode=theme_mode)
    host_stacked_html = pio.to_html(host_stacked_fig, full_html=False, include_plotlyjs=False, config={"displayModeBar": False, "responsive": True})

    host_heatmap_fig = charts.hosting_role_heatmap(data.servers.get("role_distribution", []), theme_mode=theme_mode)
    host_heatmap_html = pio.to_html(host_heatmap_fig, full_html=False, include_plotlyjs=False, config={"displayModeBar": False, "responsive": True})

    # 3. Geographic World Map
    map_fig = charts.world_map_chart(data.map_data, theme_mode=theme_mode)
    map_chart_html = pio.to_html(map_fig, full_html=False, include_plotlyjs=False, config={"displayModeBar": False, "responsive": True})

    # 4. Patch Compliance Speedometer Gauge & YTD Trend Line
    patch_pct = data.patches.get("patch_coverage_pct", 0.0)
    gauge_fig = charts.patch_gauge(
        patch_pct,
        red_limit=red_limit,
        amber_limit=amber_limit,
        green_target=green_target,
        theme_mode=theme_mode,
    )
    gauge_chart_html = pio.to_html(gauge_fig, full_html=False, include_plotlyjs=False, config={"displayModeBar": False, "responsive": True})

    ytd_trend_fig = charts.patch_compliance_ytd_trend_line(
        trend_data=custom_ytd_trend,
        green_target=green_target,
        theme_mode=theme_mode,
    )
    ytd_chart_html = pio.to_html(ytd_trend_fig, full_html=False, include_plotlyjs=False, config={"displayModeBar": False, "responsive": True})

    # Build Org Rows HTML
    org_rows_html = ""
    for r in data.org_table:
        rag_class = "rag-green" if r["rag"] == "GREEN" else "rag-amber" if r["rag"] == "AMBER" else "rag-red"
        org_rows_html += f"""
        <tr>
            <td><strong>{r['org_name']}</strong></td>
            <td>{r['region']}</td>
            <td>{r['device_count']}</td>
            <td>{r['online_pct']}%</td>
            <td>{r['patch_pct']}%</td>
            <td>{r['os_pct']}%</td>
            <td>{r['eol_count']}</td>
            <td><span class="badge {rag_class}">{r['compliance_score']}% ({r['rag']})</span></td>
        </tr>
        """

    # Build Patch Operations Rows: Top 10 Servers
    top_servers = data.sla.get("top_servers_pending_patches", [])[:10]
    top_servers_rows_html = ""
    for s in top_servers:
        top_servers_rows_html += f"""
        <tr>
            <td><strong>{s.get('name', 'N/A')}</strong></td>
            <td>{s.get('org_name', 'N/A')}</td>
            <td>{s.get('location', 'N/A')}</td>
            <td>{s.get('os_name', 'N/A')}</td>
            <td><span class="badge badge-scope">{s.get('device_role', 'Server')}</span></td>
            <td><strong style="color: var(--rag-red); font-size: 1.05rem;">{s.get('approved_patch_count', 0)}</strong></td>
        </tr>
        """

    # Build Patch Operations Rows: Top 10 Patches
    top_patches = data.sla.get("top_patches_pending_servers", [])[:10]
    top_patches_rows_html = ""
    for p_item in top_patches:
        sev = p_item.get("severity", "IMPORTANT")
        sev_class = "rag-red" if "CRIT" in sev.upper() else "rag-amber"
        top_patches_rows_html += f"""
        <tr>
            <td><strong>{p_item.get('patch_name', 'N/A')}</strong></td>
            <td><span class="badge {sev_class}">{sev}</span></td>
            <td>{p_item.get('patch_category', 'OS Security Updates')}</td>
            <td><strong>{p_item.get('pending_device_count', 0)} devices</strong></td>
            <td>{p_item.get('release_date', 'N/A')}</td>
        </tr>
        """

    # Build Patch Operations Rows: Failures Triage
    failed_rows = data.sla.get("failed_patches", [])[:20]
    failed_rows_html = ""
    for f in failed_rows:
        failed_rows_html += f"""
        <tr>
            <td><strong>{f.get('device_name', 'N/A')}</strong></td>
            <td>{f.get('org_name', 'N/A')}</td>
            <td>{f.get('location', 'N/A')}</td>
            <td>{f.get('patch_name', 'N/A')}</td>
            <td><code style="color: var(--rag-red); font-weight: 700;">{f.get('error_code', '0x80240020')}</code></td>
            <td>{f.get('failed_date', 'N/A')}</td>
            <td><span class="badge rag-amber">{f.get('attempts', 1)} attempts</span></td>
        </tr>
        """

    overall_rag_class = "rag-green" if data.compliance_rag == "GREEN" else "rag-amber" if data.compliance_rag == "AMBER" else "rag-red"

    html_content = f"""<!DOCTYPE html>
<html lang="en" data-theme="{ 'light' if is_light else 'dark' }">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} — {data.active_filter_label}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
    <style>
        :root {{
            --bg-primary: #F8FAFC;
            --bg-card: #FFFFFF;
            --bg-card-hover: #F1F5F9;
            --border: #CBD5E1;
            --text-primary: #0F172A;
            --text-secondary: #475569;
            --accent-blue: #0969DA;
            --accent-cyan: #059669;
            --rag-green: #16A34A;
            --rag-amber: #D97706;
            --rag-red: #DC2626;
            --badge-scope-bg: rgba(9, 105, 218, 0.12);
            --badge-scope-border: #0969DA;
            --badge-scope-color: #0969DA;
            --table-header-bg: #F1F5F9;
            --table-header-text: #334155;
            --table-hover-bg: #F8FAFC;
            --tab-active-bg: #0969DA;
            --tab-active-color: #FFFFFF;
        }}
        [data-theme="dark"] {{
            --bg-primary: #0D1117;
            --bg-card: #161B22;
            --bg-card-hover: #21262D;
            --border: #30363D;
            --text-primary: #E6EDF3;
            --text-secondary: #8B949E;
            --accent-blue: #2F81F7;
            --accent-cyan: #39C5BB;
            --rag-green: #2EA043;
            --rag-amber: #D29922;
            --rag-red: #CF222E;
            --badge-scope-bg: rgba(47, 129, 247, 0.2);
            --badge-scope-border: #2F81F7;
            --badge-scope-color: #2F81F7;
            --table-header-bg: #0D1117;
            --table-header-text: #8B949E;
            --table-hover-bg: #1C2128;
            --tab-active-bg: #2F81F7;
            --tab-active-color: #FFFFFF;
        }}
        body {{
            background-color: var(--bg-primary);
            color: var(--text-primary);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            padding: 0;
            margin: 0;
            transition: background-color 0.2s ease, color 0.2s ease;
        }}
        .top-navbar {{
            background-color: var(--bg-card);
            border-bottom: 1px solid var(--border);
            padding: 14px 24px;
        }}
        .nav-pills .nav-link {{
            color: var(--text-secondary);
            font-weight: 600;
            font-size: 0.92rem;
            padding: 8px 18px;
            border-radius: 8px;
            border: 1px solid transparent;
            cursor: pointer;
            transition: all 0.15s ease;
        }}
        .nav-pills .nav-link:hover {{
            background-color: var(--bg-card-hover);
            color: var(--text-primary);
        }}
        .nav-pills .nav-link.active {{
            background-color: var(--tab-active-bg) !important;
            color: var(--tab-active-color) !important;
            border-color: var(--tab-active-bg) !important;
        }}
        .kpi-card {{
            background-color: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 16px 20px;
            text-align: center;
            height: 100%;
            transition: transform 0.15s ease;
        }}
        .kpi-card:hover {{
            transform: translateY(-2px);
        }}
        .kpi-title {{
            font-size: 0.78rem;
            color: var(--text-secondary);
            text-transform: uppercase;
            font-weight: 600;
            letter-spacing: 0.05em;
            margin-bottom: 6px;
        }}
        .kpi-val {{
            font-size: 2.4rem;
            font-weight: 700;
            line-height: 1.1;
            margin-bottom: 4px;
        }}
        .chart-card {{
            background-color: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 18px;
            height: 100%;
        }}
        .chart-title {{
            font-size: 0.95rem;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 12px;
            border-bottom: 1px solid var(--border);
            padding-bottom: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .table-card {{
            background-color: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 22px;
            margin-bottom: 24px;
        }}
        .table-search-input {{
            max-width: 280px;
            font-size: 0.85rem;
            padding: 6px 12px;
            border-radius: 6px;
            border: 1px solid var(--border);
            background-color: var(--bg-primary);
            color: var(--text-primary);
        }}
        table {{
            color: var(--text-primary) !important;
        }}
        table thead th {{
            background-color: var(--table-header-bg) !important;
            color: var(--table-header-text) !important;
            border-color: var(--border) !important;
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.03em;
        }}
        table tbody td {{
            background-color: var(--bg-card) !important;
            border-color: var(--border) !important;
            color: var(--text-primary) !important;
            font-size: 0.85rem;
        }}
        table.table-hover tbody tr:hover td {{
            background-color: var(--table-hover-bg) !important;
        }}
        .badge {{
            padding: 6px 10px;
            border-radius: 6px;
            font-size: 0.75rem;
        }}
        .rag-green {{ background-color: var(--rag-green) !important; color: #fff; }}
        .rag-amber {{ background-color: var(--rag-amber) !important; color: #fff; }}
        .rag-red {{ background-color: var(--rag-red) !important; color: #fff; }}
        .badge-scope {{ background-color: var(--badge-scope-bg); color: var(--badge-scope-color); border: 1px solid var(--badge-scope-border); }}
        .btn-view-toggle {{
            font-size: 0.78rem;
            font-weight: 600;
            padding: 4px 10px;
        }}
        @media print {{
            body {{ background: #fff !important; color: #000 !important; }}
            .top-navbar, .nav-pills, .btn, .table-search-input, .report-footer {{ display: none !important; }}
            #tab-view-exec, #tab-view-ops {{ display: block !important; page-break-after: always; }}
            .chart-card, .table-card, .kpi-card {{ page-break-inside: avoid; border: 1px solid #ccc !important; }}
        }}
    </style>
</head>
<body>
    <!-- Top Header -->
    <header class="top-navbar d-flex flex-wrap justify-content-between align-items-center">
        <div class="d-flex align-items-center">
            <span style="font-size: 1.6rem; margin-right: 12px;">⚡</span>
            <div>
                <h4 class="mb-0" style="font-weight: 800; color: var(--text-primary); letter-spacing: -0.02em;">
                    NinjaOne IT Infrastructure &amp; Compliance Dashboard
                </h4>
                <div style="font-size: 0.82rem; color: var(--text-secondary); margin-top: 2px;">
                    Scope: <span class="badge badge-scope">{data.active_filter_label}</span>
                    &nbsp;&bull;&nbsp; Generated: <strong>{now_str}</strong>
                    &nbsp;&bull;&nbsp; <span style="color: var(--accent-cyan); font-weight: 600;">Offline Executive Edition</span>
                </div>
            </div>
        </div>
        <div class="d-flex align-items-center gap-2 mt-2 mt-md-0">
            <span class="badge {overall_rag_class}" style="font-size: 0.95rem; font-weight: 700; padding: 8px 14px;">
                Overall Compliance: {data.overall_compliance_score}% ({data.compliance_rag})
            </span>
            <button id="theme-toggle-btn" class="btn btn-outline-secondary btn-sm" onclick="toggleTheme()" style="font-weight: 600;">
                { '🌙 Dark' if is_light else '☀️ Light' }
            </button>
            <button class="btn btn-outline-secondary btn-sm" onclick="window.print()" style="font-weight: 600;">
                🖨️ Print / PDF
            </button>
        </div>
    </header>

    <!-- Navigation Tabs -->
    <div class="container-fluid px-4 pt-3 pb-2 border-bottom" style="background-color: var(--bg-card);">
        <ul class="nav nav-pills" id="mainDashboardTabs" role="tablist">
            <li class="nav-item me-2">
                <button class="nav-link active" id="tab-btn-exec" onclick="switchDashboardTab('exec')">
                    📊 Executive Overview
                </button>
            </li>
            <li class="nav-item">
                <button class="nav-link" id="tab-btn-ops" onclick="switchDashboardTab('ops')">
                    🛠️ Patch Operations Details
                </button>
            </li>
        </ul>
    </div>

    <!-- Main Content Container -->
    <div class="container-fluid px-4 py-4">

        <!-- ============================================================== -->
        <!-- TAB 1: EXECUTIVE OVERVIEW                                      -->
        <!-- ============================================================== -->
        <div id="tab-view-exec" class="dashboard-tab-view">
            <!-- Row 1: KPI Cards Strip -->
            <div class="row g-3 mb-4">
                <div class="col-xl-2 col-md-4 col-sm-6">
                    <div class="kpi-card">
                        <div class="kpi-title">Total Endpoints</div>
                        <div class="kpi-val">{data.total_devices:,}</div>
                        <small class="text-secondary">{data.online_devices:,} Online ({data.online_pct}%)</small>
                    </div>
                </div>
                <div class="col-xl-2 col-md-4 col-sm-6">
                    <div class="kpi-card">
                        <div class="kpi-title">Managed Servers</div>
                        <div class="kpi-val">{data.total_servers:,}</div>
                        <small class="text-secondary">{data.servers.get('windows_servers', 0)} Win &bull; {data.servers.get('linux_servers', 0)} Linux</small>
                    </div>
                </div>
                <div class="col-xl-2 col-md-4 col-sm-6">
                    <div class="kpi-card">
                        <div class="kpi-title">Patch Coverage</div>
                        <div class="kpi-val" style="color: {'var(--rag-green)' if patch_pct >= green_target else 'var(--rag-amber)' if patch_pct >= (red_limit + 1.0) else 'var(--rag-red)'};">{patch_pct:.1f}%</div>
                        <small class="text-secondary">Fleet SLA Target &ge;{int(green_target)}% (Amber &le;{int(amber_limit)}%)</small>
                    </div>
                </div>
                <div class="col-xl-2 col-md-4 col-sm-6">
                    <div class="kpi-card">
                        <div class="kpi-title">OS Supported %</div>
                        <div class="kpi-val">{data.os.get('os_compliance_pct', 0.0):.1f}%</div>
                        <small class="text-secondary">Vendor Supported OS</small>
                    </div>
                </div>
                <div class="col-xl-2 col-md-4 col-sm-6">
                    <div class="kpi-card">
                        <div class="kpi-title">EOL Hardware Risk</div>
                        <div class="kpi-val" style="color: {'var(--rag-red)' if data.eol_risk_count > 0 else 'var(--rag-green)'};">{data.eol_risk_count:,}</div>
                        <small class="text-secondary">Past / Approaching EOL</small>
                    </div>
                </div>
                <div class="col-xl-2 col-md-4 col-sm-6">
                    <div class="kpi-card">
                        <div class="kpi-title">Pending Reboots</div>
                        <div class="kpi-val" style="color: var(--rag-amber);">{len(data.sla.get('reboot_devices', [])):,}</div>
                        <small class="text-secondary">Awaiting System Restart</small>
                    </div>
                </div>
            </div>

            <!-- Row 2: OS Landscape & Patch Category Breakdown -->
            <div class="row g-3 mb-4">
                <div class="col-lg-4 col-md-6">
                    <div class="chart-card">
                        <div class="chart-title">Windows Operating Systems</div>
                        {win_chart_html}
                    </div>
                </div>
                <div class="col-lg-4 col-md-6">
                    <div class="chart-card">
                        <div class="chart-title">Linux Operating Systems</div>
                        {lin_chart_html}
                    </div>
                </div>
                <div class="col-lg-4 col-md-12">
                    <div class="chart-card">
                        <div class="chart-title">Patch Category Breakdown</div>
                        {type_chart_html}
                    </div>
                </div>
            </div>

            <!-- Row 3: Infrastructure Hosting Breakdown & World Map -->
            <div class="row g-3 mb-4">
                <div class="col-lg-6">
                    <div class="chart-card">
                        <div class="chart-title">
                            <span>Infrastructure Hosting Breakdown</span>
                            <div class="btn-group btn-group-sm" role="group">
                                <button type="button" class="btn btn-outline-primary btn-view-toggle active" id="btn-host-donut" onclick="showHostingView('donut')">Donut</button>
                                <button type="button" class="btn btn-outline-primary btn-view-toggle" id="btn-host-stacked" onclick="showHostingView('stacked')">Org Stacked</button>
                                <button type="button" class="btn btn-outline-primary btn-view-toggle" id="btn-host-heatmap" onclick="showHostingView('heatmap')">Role Heatmap</button>
                            </div>
                        </div>
                        <div id="host-view-donut">{host_donut_html}</div>
                        <div id="host-view-stacked" style="display: none;">{host_stacked_html}</div>
                        <div id="host-view-heatmap" style="display: none;">{host_heatmap_html}</div>
                    </div>
                </div>
                <div class="col-lg-6">
                    <div class="chart-card">
                        <div class="chart-title">Geographic Distribution Map</div>
                        {map_chart_html}
                    </div>
                </div>
            </div>

            <!-- Row 4: Patch Compliance Speedometer Gauge & YTD Trend -->
            <div class="row g-3 mb-4">
                <div class="col-lg-5 col-md-6">
                    <div class="chart-card">
                        <div class="chart-title">Current Month Patch Compliance</div>
                        {gauge_chart_html}
                    </div>
                </div>
                <div class="col-lg-7 col-md-6">
                    <div class="chart-card">
                        <div class="chart-title">Patch Compliance Year-to-Date (YTD) Monthly Trend</div>
                        {ytd_chart_html}
                    </div>
                </div>
            </div>

            <!-- Row 5: Organization Compliance Scorecard Table -->
            <div class="table-card">
                <div class="d-flex flex-wrap justify-content-between align-items-center mb-3 gap-2">
                    <h5 class="mb-0" style="color: var(--text-primary); font-weight: 700;">
                        🏢 Organization Compliance Scorecard
                    </h5>
                    <input type="text" id="search-org-table" class="form-control table-search-input" placeholder="🔍 Search organizations..." onkeyup="filterTable('search-org-table', 'org-scorecard-table')">
                </div>
                <div class="table-responsive">
                    <table class="table table-hover table-bordered mb-0" id="org-scorecard-table">
                        <thead>
                            <tr>
                                <th>Organization</th>
                                <th>Region</th>
                                <th>Devices</th>
                                <th>Online %</th>
                                <th>Patch %</th>
                                <th>OS %</th>
                                <th>EOL Risk</th>
                                <th>Compliance Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {org_rows_html}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- ============================================================== -->
        <!-- TAB 2: PATCH OPERATIONS DETAILS                                -->
        <!-- ============================================================== -->
        <div id="tab-view-ops" class="dashboard-tab-view" style="display: none;">
            <!-- Table 1: Top 10 Servers with Max Pending Patches -->
            <div class="table-card">
                <div class="d-flex flex-wrap justify-content-between align-items-center mb-3 gap-2">
                    <h5 class="mb-0" style="color: var(--text-primary); font-weight: 700;">
                        🚨 Top 10 Servers with Max Pending Patches
                    </h5>
                    <input type="text" id="search-servers-table" class="form-control table-search-input" placeholder="🔍 Search servers..." onkeyup="filterTable('search-servers-table', 'top-servers-table')">
                </div>
                <div class="table-responsive">
                    <table class="table table-hover table-bordered mb-0" id="top-servers-table">
                        <thead>
                            <tr>
                                <th>Server Name</th>
                                <th>Org</th>
                                <th>Loc</th>
                                <th>OS name</th>
                                <th>Device Role</th>
                                <th>Approve patch Count</th>
                            </tr>
                        </thead>
                        <tbody>
                            {top_servers_rows_html if top_servers_rows_html else '<tr><td colspan="6" class="text-center text-secondary py-3">✅ No servers with pending approved patches.</td></tr>'}
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Table 2: Top 10 Patches Pending on Max Servers -->
            <div class="table-card">
                <div class="d-flex flex-wrap justify-content-between align-items-center mb-3 gap-2">
                    <h5 class="mb-0" style="color: var(--text-primary); font-weight: 700;">
                        🩹 Top 10 Patches Pending on Max Servers
                    </h5>
                    <input type="text" id="search-patches-table" class="form-control table-search-input" placeholder="🔍 Search patches..." onkeyup="filterTable('search-patches-table', 'top-patches-table')">
                </div>
                <div class="table-responsive">
                    <table class="table table-hover table-bordered mb-0" id="top-patches-table">
                        <thead>
                            <tr>
                                <th>Patch Name</th>
                                <th>Patch Type (Critical / Important)</th>
                                <th>OS/Software type patch</th>
                                <th>Pending device count</th>
                                <th>Patch release date</th>
                            </tr>
                        </thead>
                        <tbody>
                            {top_patches_rows_html if top_patches_rows_html else '<tr><td colspan="5" class="text-center text-secondary py-3">✅ No fleet-wide pending patches.</td></tr>'}
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Table 3: Patch Deployment Failure Triage Ledger -->
            <div class="table-card">
                <div class="d-flex flex-wrap justify-content-between align-items-center mb-3 gap-2">
                    <h5 class="mb-0" style="color: var(--text-primary); font-weight: 700;">
                        ❌ Patch Deployment Failure Triage
                    </h5>
                    <input type="text" id="search-failures-table" class="form-control table-search-input" placeholder="🔍 Search failed devices or updates..." onkeyup="filterTable('search-failures-table', 'failures-table')">
                </div>
                <div class="table-responsive">
                    <table class="table table-hover table-bordered mb-0" id="failures-table">
                        <thead>
                            <tr>
                                <th>Device Name</th>
                                <th>Organization</th>
                                <th>Location</th>
                                <th>Failed Update / KB</th>
                                <th>Error Code</th>
                                <th>Last Attempt Date</th>
                                <th>Retry Attempts</th>
                            </tr>
                        </thead>
                        <tbody>
                            {failed_rows_html if failed_rows_html else '<tr><td colspan="7" class="text-center text-secondary py-3">✅ Zero patch installation failures recorded.</td></tr>'}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

    </div>

    <!-- Footer -->
    <footer class="report-footer text-center text-secondary py-4" style="border-top: 1px solid var(--border); font-size: 0.82rem; background-color: var(--bg-card);">
        NinjaOne Infrastructure &amp; Compliance Dashboard &bull; Offline Executive Snapshot &bull; Confidential
    </footer>

    <!-- Interactive Client-side Scripts -->
    <script>
        // Tab switching logic
        function switchDashboardTab(tab) {{
            const isExec = tab === 'exec';
            document.getElementById('tab-view-exec').style.display = isExec ? 'block' : 'none';
            document.getElementById('tab-view-ops').style.display = isExec ? 'none' : 'block';
            document.getElementById('tab-btn-exec').classList.toggle('active', isExec);
            document.getElementById('tab-btn-ops').classList.toggle('active', !isExec);
            window.dispatchEvent(new Event('resize'));
        }}

        // Hosting view toggle logic
        function showHostingView(view) {{
            document.getElementById('host-view-donut').style.display = view === 'donut' ? 'block' : 'none';
            document.getElementById('host-view-stacked').style.display = view === 'stacked' ? 'block' : 'none';
            document.getElementById('host-view-heatmap').style.display = view === 'heatmap' ? 'block' : 'none';
            document.getElementById('btn-host-donut').classList.toggle('active', view === 'donut');
            document.getElementById('btn-host-stacked').classList.toggle('active', view === 'stacked');
            document.getElementById('btn-host-heatmap').classList.toggle('active', view === 'heatmap');
            window.dispatchEvent(new Event('resize'));
        }}

        // Theme switching logic
        function toggleTheme() {{
            const root = document.documentElement;
            const currentTheme = root.getAttribute('data-theme') || 'light';
            const nextTheme = currentTheme === 'light' ? 'dark' : 'light';
            root.setAttribute('data-theme', nextTheme);
            document.getElementById('theme-toggle-btn').innerHTML = nextTheme === 'light' ? '🌙 Dark' : '☀️ Light';

            // Adapt Plotly chart backgrounds & text
            const isLight = nextTheme === 'light';
            const paperBg = isLight ? '#FFFFFF' : '#161B22';
            const textColor = isLight ? '#0F172A' : '#E6EDF3';
            const gridColor = isLight ? '#E2E8F0' : '#30363D';
            const update = {{
                'paper_bgcolor': paperBg,
                'plot_bgcolor': paperBg,
                'font.color': textColor,
                'xaxis.gridcolor': gridColor,
                'yaxis.gridcolor': gridColor
            }};
            document.querySelectorAll('.plotly-graph-div').forEach(el => {{
                try {{ Plotly.relayout(el, update); }} catch (e) {{}}
            }});
        }}

        // Instant table filter logic
        function filterTable(inputId, tableId) {{
            const input = document.getElementById(inputId);
            const filter = input.value.toLowerCase();
            const table = document.getElementById(tableId);
            const tr = table.getElementsByTagName('tr');
            for (let i = 1; i < tr.length; i++) {{
                const rowText = tr[i].innerText.toLowerCase();
                tr[i].style.display = rowText.includes(filter) ? '' : 'none';
            }}
        }}

        // Window resize handler for responsive Plotly graphs
        window.addEventListener('resize', () => {{
            document.querySelectorAll('.plotly-graph-div').forEach(el => {{
                try {{ Plotly.Plots.resize(el); }} catch (e) {{}}
            }});
        }});
    </script>
</body>
</html>
"""
    return html_content
