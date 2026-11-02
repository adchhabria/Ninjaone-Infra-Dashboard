"""
Standalone Executive HTML Report Generator for NinjaOne Infrastructure & Compliance Dashboard.

Generates a fully self-contained, publication-grade interactive HTML report containing
all KPI cards, interactive Plotly charts, OS Landscape & Patch Category Breakdown,
Patch Operations Details ledgers, and audit data tables.
Can be shared directly with stakeholders and opened in any web browser without needing a server.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import plotly.io as pio

from src.dashboard import charts
from src.metrics.aggregator import DashboardData


def generate_html_report(
    data: DashboardData,
    title: str = "NinjaOne Infrastructure & Compliance Audit Report",
    patch_red: float | None = None,
    patch_amber: float | None = None,
    patch_green: float | None = None,
    theme_mode: str = "dark",
) -> str:
    """
    Builds a standalone, responsive executive HTML report matching active dashboard slicers,
    active theme (dark or light), and dynamic compliance thresholds.
    """
    theme_mode = (theme_mode or "dark").lower()
    is_light = theme_mode == "light"
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Resolve dynamic compliance thresholds
    red_limit = float(patch_red if patch_red is not None else getattr(data, "patch_red", 60.0))
    amber_limit = float(patch_amber if patch_amber is not None else getattr(data, "patch_amber", 84.0))
    green_target = float(patch_green if patch_green is not None else getattr(data, "patch_green", 85.0))

    # Generate Chart HTMLs with theme_mode
    win_fig = charts.windows_os_donut(data.os.get("windows_version_counts", {}), theme_mode=theme_mode)
    win_chart_html = pio.to_html(win_fig, full_html=False, include_plotlyjs=False, config={"displayModeBar": False})

    lin_fig = charts.linux_os_donut(data.os.get("linux_version_counts", {}), theme_mode=theme_mode)
    lin_chart_html = pio.to_html(lin_fig, full_html=False, include_plotlyjs=False, config={"displayModeBar": False})

    type_counts = data.sla.get("type_counts", {})
    type_fig = charts.patch_type_donut(type_counts, theme_mode=theme_mode)
    type_chart_html = pio.to_html(type_fig, full_html=False, include_plotlyjs=False, config={"displayModeBar": False})

    host_fig = charts.hosting_donut(data.servers.get("hosting_counts", {}), theme_mode=theme_mode)
    host_chart_html = pio.to_html(host_fig, full_html=False, include_plotlyjs=False, config={"displayModeBar": False})

    stacked_fig = charts.hosting_org_stacked_bar(data.servers.get("org_distribution", []), theme_mode=theme_mode)
    stacked_chart_html = pio.to_html(stacked_fig, full_html=False, include_plotlyjs=False, config={"displayModeBar": False})

    patch_pct = data.patches.get("patch_coverage_pct", 0.0)
    gauge_fig = charts.patch_gauge(
        patch_pct,
        red_limit=red_limit,
        amber_limit=amber_limit,
        green_target=green_target,
        theme_mode=theme_mode,
    )
    gauge_chart_html = pio.to_html(gauge_fig, full_html=False, include_plotlyjs=False, config={"displayModeBar": False})

    sla_counts = data.sla.get("sla_counts", {})
    sla_fig = charts.patch_sla_aging_bar(sla_counts, theme_mode=theme_mode)
    sla_chart_html = pio.to_html(sla_fig, full_html=False, include_plotlyjs=False, config={"displayModeBar": False})

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
            <td><strong style="color: var(--rag-red);">{s.get('approved_patch_count', 0)}</strong></td>
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

    # Theme CSS variables
    if is_light:
        theme_vars = """
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
        """
    else:
        theme_vars = """
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
        """

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} — {data.active_filter_label}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
    <style>
        :root {{
{theme_vars}
        }}
        body {{
            background-color: var(--bg-primary);
            color: var(--text-primary);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
            padding: 24px 0 60px 0;
        }}
        .report-header {{
            border-bottom: 2px solid var(--border);
            padding-bottom: 18px;
            margin-bottom: 24px;
        }}
        .kpi-card {{
            background-color: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 16px 20px;
            text-align: center;
            height: 100%;
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
            font-size: 2.6rem;
            font-weight: 700;
            line-height: 1.1;
            margin-bottom: 4px;
        }}
        .chart-card {{
            background-color: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 16px;
            height: 100%;
        }}
        .chart-title {{
            font-size: 0.95rem;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 12px;
            border-bottom: 1px solid var(--border);
            padding-bottom: 8px;
        }}
        .table-card {{
            background-color: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 24px;
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
    </style>
</head>
<body>
    <div class="container-fluid px-4">
        <!-- Header -->
        <div class="report-header d-flex justify-content-between align-items-center">
            <div>
                <h3 class="mb-1" style="color: var(--text-primary); font-weight: 700;">⚡ NinjaOne IT Infrastructure & Compliance Executive Audit</h3>
                <div style="font-size: 0.85rem; color: var(--text-secondary);">
                    Generated: <strong>{now_str}</strong> &nbsp;|&nbsp; 
                    Scope: <span class="badge badge-scope">{data.active_filter_label}</span>
                </div>
            </div>
            <div class="text-end">
                <span class="badge {'rag-green' if data.compliance_rag == 'GREEN' else 'rag-amber' if data.compliance_rag == 'AMBER' else 'rag-red'}" style="font-size: 1.05rem; font-weight: 700; padding: 10px 18px;">
                    Overall Compliance: {data.overall_compliance_score}% ({data.compliance_rag})
                </span>
            </div>
        </div>

        <!-- KPI Strip -->
        <div class="row g-3 mb-4">
            <div class="col-md-2 col-sm-4 col-6">
                <div class="kpi-card">
                    <div class="kpi-title">Total Endpoints</div>
                    <div class="kpi-val">{data.total_devices:,}</div>
                    <small class="text-secondary">{data.online_devices:,} Online ({data.online_pct}%)</small>
                </div>
            </div>
            <div class="col-md-2 col-sm-4 col-6">
                <div class="kpi-card">
                    <div class="kpi-title">Managed Servers</div>
                    <div class="kpi-val">{data.total_servers:,}</div>
                    <small class="text-secondary">{data.servers.get('windows_servers', 0)} Win &bull; {data.servers.get('linux_servers', 0)} Linux</small>
                </div>
            </div>
            <div class="col-md-2 col-sm-4 col-6">
                <div class="kpi-card">
                    <div class="kpi-title">Patch Coverage</div>
                    <div class="kpi-val" style="color: {'var(--rag-green)' if patch_pct >= green_target else 'var(--rag-amber)' if patch_pct >= (red_limit + 1.0) else 'var(--rag-red)'};">{patch_pct:.1f}%</div>
                    <small class="text-secondary">Fleet SLA Target &ge;{int(green_target)}% (Amber &le;{int(amber_limit)}%)</small>
                </div>
            </div>
            <div class="col-md-2 col-sm-4 col-6">
                <div class="kpi-card">
                    <div class="kpi-title">OS Supported %</div>
                    <div class="kpi-val">{data.os.get('os_compliance_pct', 0.0):.1f}%</div>
                    <small class="text-secondary">Vendor Supported OS</small>
                </div>
            </div>
            <div class="col-md-2 col-sm-4 col-6">
                <div class="kpi-card">
                    <div class="kpi-title">EOL Hardware Risk</div>
                    <div class="kpi-val" style="color: {'var(--rag-red)' if data.eol_risk_count > 0 else 'var(--rag-green)'};">{data.eol_risk_count:,}</div>
                    <small class="text-secondary">Past / Approaching EOL</small>
                </div>
            </div>
            <div class="col-md-2 col-sm-4 col-6">
                <div class="kpi-card">
                    <div class="kpi-title">Pending Reboots</div>
                    <div class="kpi-val" style="color: var(--rag-amber);">{len(data.sla.get('reboot_devices', [])):,}</div>
                    <small class="text-secondary">Awaiting System Restart</small>
                </div>
            </div>
        </div>

        <!-- Section 1: Operating System Landscape & Patch Category Breakdown -->
        <div class="row g-3 mb-4">
            <div class="col-md-4">
                <div class="chart-card">
                    <div class="chart-title">Windows Operating Systems</div>
                    {win_chart_html}
                </div>
            </div>
            <div class="col-md-4">
                <div class="chart-card">
                    <div class="chart-title">Linux Operating Systems</div>
                    {lin_chart_html}
                </div>
            </div>
            <div class="col-md-4">
                <div class="chart-card">
                    <div class="chart-title">Patch Category Breakdown</div>
                    {type_chart_html}
                </div>
            </div>
        </div>

        <!-- Section 2: Hosting & Compliance Speedometer -->
        <div class="row g-3 mb-4">
            <div class="col-md-4">
                <div class="chart-card">
                    <div class="chart-title">Current Month Patch Compliance</div>
                    {gauge_chart_html}
                </div>
            </div>
            <div class="col-md-4">
                <div class="chart-card">
                    <div class="chart-title">Multi-Cloud Server Hosting Breakdown</div>
                    {host_chart_html}
                </div>
            </div>
            <div class="col-md-4">
                <div class="chart-card">
                    <div class="chart-title">Organization-Wise Hosting Distribution</div>
                    {stacked_chart_html}
                </div>
            </div>
        </div>

        <!-- Section 3: Patch Operations Details & Failure Triage -->
        <div class="table-card">
            <h5 class="mb-3" style="color: var(--text-primary); font-weight: 600;">🚨 Top 10 Servers with Max Pending Patches</h5>
            <div class="table-responsive">
                <table class="table table-hover table-bordered mb-0">
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

        <div class="table-card">
            <h5 class="mb-3" style="color: var(--text-primary); font-weight: 600;">🩹 Top 10 Patches Pending on Max Servers</h5>
            <div class="table-responsive">
                <table class="table table-hover table-bordered mb-0">
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

        <div class="table-card">
            <h5 class="mb-3" style="color: var(--text-primary); font-weight: 600;">❌ Patch Deployment Failure Triage</h5>
            <div class="table-responsive">
                <table class="table table-hover table-bordered mb-0">
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

        <!-- Section 4: Organization Compliance Matrix -->
        <div class="table-card">
            <h5 class="mb-3" style="color: var(--text-primary); font-weight: 600;">🏢 Organization Compliance Scorecard</h5>
            <div class="table-responsive">
                <table class="table table-hover table-bordered mb-0">
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

        <!-- Footer -->
        <div class="text-center text-secondary mt-5" style="font-size: 0.8rem;">
            Generated by NinjaOne Infrastructure & Compliance Dashboard &bull; Confidential
        </div>
    </div>
</body>
</html>
"""
    return html_content
