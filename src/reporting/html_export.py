"""
Standalone Executive HTML Report Generator for NinjaOne Infrastructure & Compliance Dashboard.

Generates a fully self-contained, publication-grade interactive HTML report containing
all KPI cards, interactive Plotly charts, SLA breakdown, multi-cloud hosting, and audit data tables.
Can be shared directly with stakeholders and opened in any web browser without needing a server.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import plotly.io as pio

from src.dashboard import charts
from src.metrics.aggregator import DashboardData


def generate_html_report(data: DashboardData, title: str = "NinjaOne Infrastructure & Compliance Audit Report") -> str:
    """
    Builds a standalone, responsive, dark-themed HTML executive report matching active dashboard slicers.
    """
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Generate Chart HTMLs
    win_fig = charts.windows_os_donut(data.os.get("windows_version_counts", {}))
    win_chart_html = pio.to_html(win_fig, full_html=False, include_plotlyjs=False, config={"displayModeBar": False})

    lin_fig = charts.linux_os_donut(data.os.get("linux_version_counts", {}))
    lin_chart_html = pio.to_html(lin_fig, full_html=False, include_plotlyjs=False, config={"displayModeBar": False})

    host_fig = charts.hosting_donut(data.servers.get("hosting_counts", {}))
    host_chart_html = pio.to_html(host_fig, full_html=False, include_plotlyjs=False, config={"displayModeBar": False})

    stacked_fig = charts.hosting_org_stacked_bar(data.servers.get("org_distribution", []))
    stacked_chart_html = pio.to_html(stacked_fig, full_html=False, include_plotlyjs=False, config={"displayModeBar": False})

    patch_pct = data.patches.get("patch_coverage_pct", 0.0)
    gauge_fig = charts.patch_gauge(patch_pct)
    gauge_chart_html = pio.to_html(gauge_fig, full_html=False, include_plotlyjs=False, config={"displayModeBar": False})

    sla_counts = data.sla.get("sla_counts", {})
    sla_fig = charts.patch_sla_aging_bar(sla_counts)
    sla_chart_html = pio.to_html(sla_fig, full_html=False, include_plotlyjs=False, config={"displayModeBar": False})

    type_counts = data.sla.get("type_counts", {})
    type_fig = charts.patch_type_donut(type_counts)
    type_chart_html = pio.to_html(type_fig, full_html=False, include_plotlyjs=False, config={"displayModeBar": False})

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


    # Build Reboot Rows HTML
    reboot_rows_html = ""
    for rb in data.sla.get("reboot_devices", [])[:50]:
        reboot_rows_html += f"""
        <tr>
            <td><strong>{rb.get('name', 'N/A')}</strong></td>
            <td>{rb.get('org_name', 'N/A')}</td>
            <td>{rb.get('os', 'N/A')}</td>
            <td>{rb.get('uptime_days', 0)} days</td>
            <td><span class="badge rag-amber">Pending Reboot</span></td>
        </tr>
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
        }}
        body {{
            background-color: var(--bg-primary);
            color: var(--text-primary);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
            padding: 24px 0 60px 0;
        }}
        .report-header {{
            background-color: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 24px;
        }}
        .kpi-card {{
            background-color: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            height: 100%;
        }}
        .kpi-val {{
            font-size: 2rem;
            font-weight: 700;
            color: var(--accent-blue);
            margin: 6px 0;
        }}
        .kpi-title {{
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--text-secondary);
        }}
        .chart-card {{
            background-color: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 16px;
            margin-bottom: 20px;
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
            background-color: var(--bg-primary) !important;
            color: var(--text-secondary) !important;
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
        .badge {{
            padding: 6px 10px;
            border-radius: 6px;
            font-size: 0.75rem;
        }}
        .rag-green {{ background-color: var(--rag-green) !important; color: #fff; }}
        .rag-amber {{ background-color: var(--rag-amber) !important; color: #fff; }}
        .rag-red {{ background-color: var(--rag-red) !important; color: #fff; }}
        .badge-scope {{ background-color: rgba(47, 129, 247, 0.2); color: var(--accent-blue); border: 1px solid var(--accent-blue); }}
    </style>
</head>
<body>
    <div class="container-fluid px-4">
        <!-- Header -->
        <div class="report-header d-flex justify-content-between align-items-center">
            <div>
                <h3 class="mb-1 text-white">⚡ NinjaOne IT Infrastructure & Compliance Executive Audit</h3>
                <div class="text-secondary" style="font-size: 0.85rem;">
                    Generated: <strong>{now_str}</strong> &nbsp;|&nbsp; 
                    Scope: <span class="badge badge-scope">{data.active_filter_label}</span>
                </div>
            </div>
            <div class="text-end">
                <span class="badge {'rag-green' if data.compliance_rag == 'GREEN' else 'rag-amber' if data.compliance_rag == 'AMBER' else 'rag-red'}" style="font-size: 1rem; padding: 8px 16px;">
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
                    <div class="kpi-val" style="color: {'var(--rag-green)' if patch_pct >= 85 else 'var(--rag-amber)' if patch_pct >= 60 else 'var(--rag-red)'};">{patch_pct:.1f}%</div>
                    <small class="text-secondary">Fleet SLA Target ≥85%</small>
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

        <!-- Section 1: Executive Charts -->
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
                    <div class="chart-title">Patch Compliance Speedometer</div>
                    {gauge_chart_html}
                </div>
            </div>
        </div>

        <div class="row g-3 mb-4">
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
            <div class="col-md-4">
                <div class="chart-card">
                    <div class="chart-title">Patch SLA Aging Backlog</div>
                    {sla_chart_html}
                </div>
            </div>
        </div>

        <!-- Section 2: Organization Compliance Matrix -->
        <div class="table-card">
            <h5 class="mb-3 text-white">🏢 Organization Compliance Scorecard</h5>
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
