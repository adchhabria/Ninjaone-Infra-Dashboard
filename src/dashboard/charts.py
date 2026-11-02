"""
Plotly chart builders for the NinjaOne dashboard.

All figures use the shared dark theme for consistent visual hierarchy.
Includes:
- World Map with hover-only tooltip inspection
- 2 Separate Donut charts for Windows and Linux OS distributions
- Server Role Breakdown & Multi-Cloud/VM Hosting Donut & Heatmap
- Speedometer Patch Gauge with 85% Green Threshold
- Patch SLA Aging & Category charts
"""

from __future__ import annotations

from datetime import datetime, date
from typing import Any, Optional

import plotly.graph_objects as go
import pandas as pd

from src.dashboard import theme as T


def _apply_theme(fig: go.Figure, title: str = "", theme_mode: str = "dark") -> go.Figure:
    """Apply the shared theme template (dark or light) and optional title to any figure."""
    tmpl = T.get_plotly_template(theme_mode)
    p = T.get_theme_palette(theme_mode)
    fig.update_layout(**tmpl["layout"])
    fig.update_layout(
        paper_bgcolor=p["bg_card"],
        plot_bgcolor=p["bg_card"],
        font=dict(family="Inter, -apple-system, sans-serif", color=p["text_primary"], size=12),
        legend=dict(
            bgcolor=p["bg_card"],
            bordercolor=p["border"],
            borderwidth=1,
            font=dict(color=p["text_secondary"], size=11),
        ),
    )
    if title:
        fig.update_layout(title_text=title, title_font=dict(color=p["text_primary"], size=14))
    return fig


# ---------------------------------------------------------------------------
# World Map / Geographic Chart (Hover-only text display)
# ---------------------------------------------------------------------------

def world_map_chart(map_data: list[dict], selected_region: Optional[str] = None, theme_mode: str = "dark") -> go.Figure:
    """
    Renders an interactive world map.
    Only shows data tooltips when hovering over marker circles.
    """
    p = T.get_theme_palette(theme_mode)
    if not map_data:
        return _empty_figure("No geographic data available", theme_mode=theme_mode)

    # Marker colors based on RAG status
    colors = [
        T.RAG_GREEN if r.get("rag") == "GREEN" else T.RAG_AMBER if r.get("rag") == "AMBER" else T.RAG_RED
        for r in map_data
    ]

    # Marker sizes scaled proportionally by device count (diameter reflects volume)
    raw_counts = [r.get("device_count", 0) for r in map_data]
    max_devs = max(raw_counts) if raw_counts and max(raw_counts) > 0 else 1
    sizes = [14 + (count / max_devs) * 36 for count in raw_counts]

    hover_texts = [
        f"<b>{r.get('country_name', 'Unknown')}</b><br>"
        f"Region: {r.get('region', 'N/A')}<br>"
        f"Devices: <b>{r.get('device_count', 0)}</b> across {r.get('org_count', 0)} orgs<br>"
        f"Compliance: <b>{r.get('compliance_score', 0.0)}%</b> ({r.get('rag', 'RED')})<br>"
        f"EOL Devices: {r.get('eol_count', 0)}"
        for r in map_data
    ]

    fig = go.Figure()

    # Geo scatter points — mode='markers' (shows text ONLY on hover)
    fig.add_trace(
        go.Scattergeo(
            lat=[r.get("lat", 0.0) for r in map_data],
            lon=[r.get("lon", 0.0) for r in map_data],
            text=hover_texts,
            hoverinfo="text",
            mode="markers",
            marker=dict(
                size=sizes,
                color=colors,
                line=dict(width=2, color=p["text_primary"]),
                opacity=0.88,
            ),
            customdata=[r.get("region", "") for r in map_data],
        )
    )

    # Geo layout configuration
    geo_config: dict[str, Any] = dict(
        bgcolor=p["bg_card"],
        showland=True,
        landcolor="#F1F5F9" if not p["is_dark"] else "#1F242C",
        showocean=True,
        oceancolor=p["bg_card"],
        showlakes=True,
        lakecolor=p["bg_card"],
        showcountries=True,
        countrycolor=p["border"],
        coastlinecolor=p["border"],
        projection_type="natural earth",
        resolution=110,
    )

    # Region focus zoom or single-country focus zoom
    if len(map_data) == 1:
        geo_config["center"] = dict(lat=map_data[0].get("lat", 20), lon=map_data[0].get("lon", 0))
        geo_config["projection_scale"] = 3.6
    elif selected_region == "APAC / Asia":
        geo_config["center"] = dict(lat=20, lon=105)
        geo_config["projection_scale"] = 2.2
    elif selected_region == "USA / North America":
        geo_config["center"] = dict(lat=40, lon=-100)
        geo_config["projection_scale"] = 2.4
    elif selected_region == "EMEA / Europe":
        geo_config["center"] = dict(lat=52, lon=15)
        geo_config["projection_scale"] = 3.0
    elif selected_region == "Latin America":
        geo_config["center"] = dict(lat=-15, lon=-60)
        geo_config["projection_scale"] = 2.0

    fig.update_layout(
        geo=geo_config,
        margin=dict(l=0, r=0, t=30, b=0),
        height=320,
    )

    return _apply_theme(fig, "Global Device Infrastructure & Compliance Map", theme_mode=theme_mode)


# ---------------------------------------------------------------------------
# OS Distribution Charts (2 Separate Donuts: Windows & Linux)
# ---------------------------------------------------------------------------

def windows_os_donut(windows_version_counts: dict[str, int], theme_mode: str = "dark") -> go.Figure:
    """Donut chart — Granular Windows OS builds breakdown."""
    p = T.get_theme_palette(theme_mode)
    if not windows_version_counts:
        return _empty_figure("No Windows devices found", theme_mode=theme_mode)

    labels = list(windows_version_counts.keys())
    values = list(windows_version_counts.values())

    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.60,
            marker=dict(line=dict(color=p["bg_card"], width=2)),
            textinfo="none",
            hovertemplate="<b>%{label}</b><br>%{value} Windows devices (%{percent})<extra></extra>",
        )
    )
    fig.update_layout(showlegend=True, height=285, margin=dict(t=30, b=15, l=15, r=15))
    return _apply_theme(fig, "Windows OS Builds Breakdown", theme_mode=theme_mode)


def linux_os_donut(linux_version_counts: dict[str, int], theme_mode: str = "dark") -> go.Figure:
    """Donut chart — Granular Linux distributions breakdown."""
    p = T.get_theme_palette(theme_mode)
    if not linux_version_counts:
        return _empty_figure("No Linux devices found", theme_mode=theme_mode)

    labels = list(linux_version_counts.keys())
    values = list(linux_version_counts.values())

    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.60,
            marker=dict(line=dict(color=p["bg_card"], width=2)),
            textinfo="none",
            hovertemplate="<b>%{label}</b><br>%{value} Linux systems (%{percent})<extra></extra>",
        )
    )
    fig.update_layout(showlegend=True, height=285, margin=dict(t=30, b=15, l=15, r=15))
    return _apply_theme(fig, "Linux Distributions Breakdown", theme_mode=theme_mode)


# ---------------------------------------------------------------------------
# Dedicated End-of-Life (EOL) Charts
# ---------------------------------------------------------------------------

def eol_status_donut(eol_status_counts: dict[str, int], theme_mode: str = "dark") -> go.Figure:
    """Donut chart — Supported vs Approaching EOL vs Expired."""
    p = T.get_theme_palette(theme_mode)
    labels = ["Supported", "Approaching EOL", "Expired (EOL)"]
    values = [eol_status_counts.get(l, 0) for l in labels]
    colors = [T.RAG_GREEN, T.RAG_AMBER, T.RAG_RED]

    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.62,
            marker=dict(colors=colors, line=dict(color=p["bg_card"], width=2)),
            textinfo="none",
            hovertemplate="<b>%{label}</b><br>%{value} devices (%{percent})<extra></extra>",
        )
    )
    fig.update_layout(showlegend=True, height=255, margin=dict(t=30, b=15, l=15, r=15))
    return _apply_theme(fig, "Lifecycle & Support Status", theme_mode=theme_mode)


def eol_by_os_bar(eol_by_os_counts: dict[str, int], theme_mode: str = "dark") -> go.Figure:
    """Horizontal bar — distribution of devices on obsolete/at-risk OS versions."""
    p = T.get_theme_palette(theme_mode)
    if not eol_by_os_counts:
        return _empty_figure("✅ No EOL or Approaching-EOL devices found", theme_mode=theme_mode)

    sorted_items = sorted(eol_by_os_counts.items(), key=lambda x: x[1], reverse=True)[:8]
    labels = [i[0] for i in reversed(sorted_items)]
    values = [i[1] for i in reversed(sorted_items)]

    fig = go.Figure(
        go.Bar(
            y=labels,
            x=values,
            orientation="h",
            marker=dict(color=T.RAG_RED, line=dict(color=p["bg_card"], width=1)),
            hovertemplate="<b>%{y}</b><br>%{x} at-risk devices<extra></extra>",
        )
    )
    fig.update_layout(
        xaxis_title="Affected Devices",
        yaxis_title="",
        height=250,
        xaxis=dict(tickfont=dict(color=p["text_secondary"]), title=dict(font=dict(color=p["text_secondary"]))),
        yaxis=dict(tickfont=dict(color=p["text_secondary"])),
    )
    return _apply_theme(fig, "At-Risk OS Versions", theme_mode=theme_mode)


# ---------------------------------------------------------------------------
# Server / Hosting Charts
# ---------------------------------------------------------------------------

def server_role_bar(role_counts: dict[str, int], theme_mode: str = "dark") -> go.Figure:
    """Horizontal bar — servers by role."""
    p = T.get_theme_palette(theme_mode)
    sorted_items = sorted(role_counts.items(), key=lambda x: x[1], reverse=True)
    labels = [i[0] for i in reversed(sorted_items)]
    values = [i[1] for i in reversed(sorted_items)]

    fig = go.Figure(
        go.Bar(
            y=labels,
            x=values,
            orientation="h",
            marker=dict(
                color=T.ACCENT_PURPLE,
                line=dict(color=p["bg_card"], width=1),
            ),
            hovertemplate="<b>%{y}</b><br>%{x} servers<extra></extra>",
        )
    )
    fig.update_layout(
        xaxis_title="Count",
        yaxis_title="",
        height=270,
        xaxis=dict(tickfont=dict(color=p["text_secondary"]), title=dict(font=dict(color=p["text_secondary"]))),
        yaxis=dict(tickfont=dict(color=p["text_secondary"])),
    )
    return _apply_theme(fig, "Server Role Distribution", theme_mode=theme_mode)


def hosting_donut(hosting_counts: dict[str, int], filter_mode: str = "all", theme_mode: str = "dark") -> go.Figure:
    """Donut chart for hosting types supporting filter_mode: 'all', 'onprem', 'cloud'."""
    p = T.get_theme_palette(theme_mode)
    CANONICAL_HOSTING = ["Azure Server", "AWS Server", "VM Server", "Physical Server"]
    if filter_mode == "cloud":
        target_keys = ["Azure Server", "AWS Server"]
        title = "Cloud Infrastructure (Azure & AWS)"
    elif filter_mode == "onprem":
        target_keys = ["Physical Server", "VM Server"]
        title = "On-Premise Infrastructure (Physical & VMs)"
    else:
        target_keys = CANONICAL_HOSTING
        title = "All Devices Hosting Infrastructure"

    filtered_counts = {k: hosting_counts[k] for k in target_keys if hosting_counts.get(k, 0) > 0}

    if not filtered_counts:
        return _empty_figure(f"No devices found for {filter_mode.title()} filter", theme_mode=theme_mode)

    labels = list(filtered_counts.keys())
    values = list(filtered_counts.values())
    colors = [T.HOSTING_COLORS.get(l, T.ACCENT_BLUE) for l in labels]

    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.60,
            marker=dict(colors=colors, line=dict(color=p["bg_card"], width=2)),
            textinfo="none",
            hovertemplate="<b>%{label}</b><br>%{value} devices (%{percent})<extra></extra>",
        )
    )
    fig.update_layout(showlegend=True, height=285, margin=dict(t=30, b=15, l=15, r=15))
    return _apply_theme(fig, title, theme_mode=theme_mode)


def hosting_org_stacked_bar(org_distribution: list[dict], filter_mode: str = "all", theme_mode: str = "dark") -> go.Figure:
    """
    Organization-wise stacked bar chart showing device distribution.
    Supports filter_mode: 'all', 'onprem', 'cloud'.
    """
    p = T.get_theme_palette(theme_mode)
    if not org_distribution:
        return _empty_figure("No organization hosting data available", theme_mode=theme_mode)

    top_orgs = org_distribution[:15]
    org_names = [o["org_name"] for o in top_orgs]

    fig = go.Figure()

    if filter_mode in ["all", "cloud"]:
        fig.add_trace(
            go.Bar(
                name="Azure Server",
                x=org_names,
                y=[o.get("azure", 0) for o in top_orgs],
                marker_color=T.HOSTING_COLORS.get("Azure Server", "#0089D6"),
                hovertemplate="<b>%{x}</b><br>Azure: %{y}<extra></extra>",
            )
        )
        fig.add_trace(
            go.Bar(
                name="AWS Server",
                x=org_names,
                y=[o.get("aws", 0) for o in top_orgs],
                marker_color=T.HOSTING_COLORS.get("AWS Server", "#FF9900"),
                hovertemplate="<b>%{x}</b><br>AWS: %{y}<extra></extra>",
            )
        )

    if filter_mode in ["all", "onprem"]:
        fig.add_trace(
            go.Bar(
                name="VM Server",
                x=org_names,
                y=[o.get("vm", 0) for o in top_orgs],
                marker_color=T.HOSTING_COLORS.get("VM Server", "#39C5BB"),
                hovertemplate="<b>%{x}</b><br>VM: %{y}<extra></extra>",
            )
        )
        fig.add_trace(
            go.Bar(
                name="Physical Server",
                x=org_names,
                y=[o.get("physical", 0) for o in top_orgs],
                marker_color=T.HOSTING_COLORS.get("Physical Server", "#8B949E"),
                hovertemplate="<b>%{x}</b><br>Physical: %{y}<extra></extra>",
            )
        )

    fig.update_layout(
        barmode="stack",
        height=270,
        xaxis=dict(tickangle=-30, tickfont=dict(size=10, color=p["text_secondary"])),
        yaxis=dict(title="Device Count", title_font=dict(color=p["text_secondary"]), tickfont=dict(color=p["text_secondary"])),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color=p["text_secondary"])),
    )
    return _apply_theme(fig, "Organization-wise Hosting Distribution", theme_mode=theme_mode)


def hosting_role_heatmap(matrix: list[dict], theme_mode: str = "dark") -> go.Figure:
    """Heatmap — Hosting × Server Role device counts."""
    p = T.get_theme_palette(theme_mode)
    if not matrix:
        return _empty_figure("No server hosting data available", theme_mode=theme_mode)

    df = pd.DataFrame(matrix)
    pivot = df.pivot_table(index="hosting", columns="role", values="count", fill_value=0)

    fig = go.Figure(
        go.Heatmap(
            z=pivot.values,
            x=pivot.columns.tolist(),
            y=pivot.index.tolist(),
            colorscale=[[0, p["bg_card"]], [0.5, T.ACCENT_BLUE], [1, T.ACCENT_PURPLE]],
            showscale=True,
            hovertemplate="<b>%{y} × %{x}</b><br>%{z} servers<extra></extra>",
            text=pivot.values,
            texttemplate="%{text}",
            textfont=dict(color=p["text_primary"], size=10),
        )
    )
    fig.update_layout(height=220)
    return _apply_theme(fig, "Hosting × Role Matrix", theme_mode=theme_mode)


# ---------------------------------------------------------------------------
# Patch Compliance Gauge (0-60 Red, 61-84 Amber, 85+ Green)
# ---------------------------------------------------------------------------

DEFAULT_YTD_TREND: dict[str, float] = {
    "Oct-25": 80.0,
    "Nov-25": 82.0,
    "Dec-25": 90.0,
    "Jan-26": 85.0,
    "Feb-26": 88.0,
    "Mar-26": 74.0,
    "Apr-26": 95.0,
    "May-26": 90.0,
    "Jun-26": 50.0,
    "Jul-26": 70.0,
    "Aug-26": 85.0,
    "Sep-26": 96.0,
    "Oct-26": 90.0,
}


def get_patch_cycle_current_month(ref_date: datetime | date | None = None) -> tuple[int, int]:
    """
    Returns (year, month) of the current completed patching cycle.
    The current compliance cycle being published is N-1 (the previous calendar month based on today's date).
    For example, on November 2, 2026, the current completed month is October 2026.
    """
    if ref_date is None:
        ref_date = datetime.now().date()
    elif isinstance(ref_date, datetime):
        ref_date = ref_date.date()

    year = ref_date.year
    month = ref_date.month

    # Always N-1 relative to today's month
    total_months = year * 12 + (month - 1) - 1
    cycle_year = total_months // 12
    cycle_month = (total_months % 12) + 1
    return cycle_year, cycle_month


def get_patch_cycle_12_months(ref_date: datetime | date | None = None) -> list[str]:
    """
    Returns the 12 rolling months ending at the current completed patching cycle (N-1),
    formatted as 'MMM-YY' (e.g., ['Nov-25', 'Dec-25', ..., 'Oct-26']).
    """
    cycle_year, cycle_month = get_patch_cycle_current_month(ref_date)
    months = []
    for i in range(11, -1, -1):
        total = cycle_year * 12 + (cycle_month - 1) - i
        y = total // 12
        m = (total % 12) + 1
        d = date(y, m, 1)
        months.append(d.strftime("%b-%y"))
    return months


def patch_gauge(
    patch_pct: float,
    red_limit: float = 60.0,
    amber_limit: float = 90.0,
    green_target: float = 90.0,
    theme_mode: str = "light",
) -> go.Figure:
    """
    Speedometer gauge — overall patch coverage % with 5-point meter bar divisions.
    Solid RAG color steps: Red (0 to red_limit), Amber (red_limit to amber_limit), Green (amber_limit to 100).
    Title: 'Current month patch compliance'.
    Default thresholds: Red Max = 60%, Amber Max = 90%, Green Target = 90%.
    """
    p = T.get_theme_palette(theme_mode)
    color = (
        T.RAG_GREEN if patch_pct >= green_target
        else T.RAG_AMBER if patch_pct >= (red_limit + 1.0)
        else T.RAG_RED
    )

    # Distinct needle / bar indicator
    needle_color = "#0F172A" if theme_mode == "light" else "#FFFFFF"

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number+delta",
            value=patch_pct,
            number=dict(suffix="%", font=dict(size=40, color=color)),
            delta=dict(reference=green_target, valueformat=".1f", font=dict(color=p["text_secondary"])),
            gauge=dict(
                axis=dict(
                    range=[0, 100],
                    tickmode="linear",
                    tick0=0,
                    dtick=5,  # 5-point meter bar divisions
                    ticks="inside",
                    tickcolor=p["text_secondary"],
                    tickfont=dict(color=p["text_secondary"], size=9),
                ),
                bar=dict(color=needle_color, thickness=0.26),
                bgcolor=p["bg_card"],
                bordercolor=p["border"],
                steps=[
                    dict(range=[0, red_limit], color="#DC2626"),          # Solid Vivid RED
                    dict(range=[red_limit, amber_limit], color="#F59E0B"), # Solid Vivid AMBER
                    dict(range=[amber_limit, 100], color="#16A34A"),      # Solid Vivid GREEN
                ],
                threshold=dict(
                    line=dict(color=p["text_primary"], width=2.5),
                    thickness=0.75,
                    value=green_target,
                ),
            ),
        )
    )
    fig.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=260)
    return _apply_theme(fig, "Current month patch compliance", theme_mode=theme_mode)


def patch_compliance_ytd_trend_line(
    trend_data: dict[str, float] | None = None,
    green_target: float = 90.0,
    theme_mode: str = "light",
    ref_date: datetime | date | None = None,
) -> go.Figure:
    """
    Line chart — Year-to-Date (YTD) Patch Compliance trend over 12 rolling months
    aligned to the enterprise patching cycle (N-1 from today's date).
    """
    p = T.get_theme_palette(theme_mode)
    rolling_months = get_patch_cycle_12_months(ref_date)
    user_data = trend_data or DEFAULT_YTD_TREND

    months = rolling_months
    values = []
    for m in months:
        if m in user_data:
            values.append(float(user_data[m]))
        elif m in DEFAULT_YTD_TREND:
            values.append(float(DEFAULT_YTD_TREND[m]))
        else:
            values.append(85.0)

    fig = go.Figure()

    # Target Benchmark Line (e.g. 90%)
    fig.add_trace(
        go.Scatter(
            x=months,
            y=[green_target] * len(months),
            mode="lines",
            name=f"Target ({int(green_target)}%)",
            line=dict(color="#10B981" if theme_mode == "dark" else "#059669", width=2, dash="dash"),
            hoverinfo="none",
        )
    )

    # Actual Compliance Trend Line with shaded fill
    line_color = "#38BDF8" if theme_mode == "dark" else "#2563EB"
    fill_color = "rgba(56, 189, 248, 0.12)" if theme_mode == "dark" else "rgba(37, 99, 235, 0.08)"

    # Point marker colors: Green if >= target, Amber if >= 70, Red if < 70
    marker_colors = [
        T.RAG_GREEN if v >= green_target else (T.RAG_AMBER if v >= 70.0 else T.RAG_RED)
        for v in values
    ]

    fig.add_trace(
        go.Scatter(
            x=months,
            y=values,
            mode="lines+markers",
            name="Compliance %",
            line=dict(color=line_color, width=3, shape="spline"),
            marker=dict(
                size=8,
                color=marker_colors,
                line=dict(color="#FFFFFF" if theme_mode == "dark" else "#1E293B", width=1.5),
            ),
            fill="tozeroy",
            fillcolor=fill_color,
            hovertemplate="<b>%{x}</b><br>Compliance: <b>%{y:.1f}%</b><extra></extra>",
        )
    )

    fig.update_layout(
        yaxis=dict(
            range=[30, 110],
            ticksuffix="%",
            gridcolor=p["border"],
            zerolinecolor=p["border"],
            tickfont=dict(color=p["text_secondary"], size=10),
        ),
        xaxis=dict(
            gridcolor="rgba(0,0,0,0)",
            tickfont=dict(color=p["text_secondary"], size=10),
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=10, color=p["text_secondary"]),
        ),
        margin=dict(l=35, r=20, t=35, b=25),
        height=260,
    )

    return _apply_theme(fig, "Patch Compliance Year-to-Date (YTD) Trend", theme_mode=theme_mode)


# ---------------------------------------------------------------------------
# Patch SLA Aging & Classification Charts
# ---------------------------------------------------------------------------

def patch_sla_aging_bar(sla_counts: dict[str, int], theme_mode: str = "dark") -> go.Figure:
    """Bar chart — Distribution of pending patches across SLA aging brackets."""
    p = T.get_theme_palette(theme_mode)
    labels = [
        "< 7 Days (Within SLA)",
        "8 - 30 Days (Warning)",
        "31 - 90 Days (High Risk)",
        "> 90 Days (SLA Breach)",
    ]
    values = [sla_counts.get(l, 0) for l in labels]
    colors = [T.RAG_GREEN, T.RAG_AMBER, "#FF9800", T.RAG_RED]

    fig = go.Figure(
        go.Bar(
            x=labels,
            y=values,
            marker=dict(color=colors, line=dict(color=p["bg_card"], width=1)),
            hovertemplate="<b>%{x}</b><br>%{y} pending patches<extra></extra>",
        )
    )
    fig.update_layout(
        xaxis_title="",
        yaxis_title="Pending Patches",
        height=250,
        xaxis=dict(tickfont=dict(color=p["text_secondary"])),
        yaxis=dict(tickfont=dict(color=p["text_secondary"]), title=dict(font=dict(color=p["text_secondary"]))),
    )
    return _apply_theme(fig, "Patch SLA Aging Backlog", theme_mode=theme_mode)


def patch_type_donut(type_counts: dict[str, int], theme_mode: str = "dark") -> go.Figure:
    """Donut chart — OS Security Patches vs 3rd-Party Applications."""
    p = T.get_theme_palette(theme_mode)
    labels = list(type_counts.keys())
    values = list(type_counts.values())
    colors = [T.ACCENT_BLUE, T.ACCENT_PURPLE, T.ACCENT_TEAL]

    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.60,
            marker=dict(colors=colors, line=dict(color=p["bg_card"], width=2)),
            textinfo="none",
            hovertemplate="<b>%{label}</b><br>%{value} patches (%{percent})<extra></extra>",
        )
    )
    fig.update_layout(showlegend=True, height=285, margin=dict(t=30, b=15, l=15, r=15))
    return _apply_theme(fig, "Patch Category Breakdown", theme_mode=theme_mode)


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _empty_figure(message: str = "No data", theme_mode: str = "dark") -> go.Figure:
    """Placeholder figure shown when data is absent."""
    p = T.get_theme_palette(theme_mode)
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(color=p["text_muted"], size=13),
    )
    fig.update_layout(xaxis=dict(visible=False), yaxis=dict(visible=False), height=220)
    return _apply_theme(fig, theme_mode=theme_mode)
