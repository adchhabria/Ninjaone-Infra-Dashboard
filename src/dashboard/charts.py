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

from typing import Any, Optional

import plotly.graph_objects as go
import pandas as pd

from src.dashboard import theme as T


def _apply_theme(fig: go.Figure, title: str = "") -> go.Figure:
    """Apply the shared dark template and optional title to any figure."""
    fig.update_layout(**T.PLOTLY_TEMPLATE["layout"])
    if title:
        fig.update_layout(title_text=title)
    return fig


# ---------------------------------------------------------------------------
# World Map / Geographic Chart (Hover-only text display)
# ---------------------------------------------------------------------------

def world_map_chart(map_data: list[dict], selected_region: Optional[str] = None) -> go.Figure:
    """
    Renders an interactive dark world map.
    Only shows data tooltips when hovering over marker circles.
    """
    if not map_data:
        return _empty_figure("No geographic data available")

    df = pd.DataFrame(map_data)

    # Marker colors based on RAG status
    colors = [
        T.RAG_GREEN if r == "GREEN" else T.RAG_AMBER if r == "AMBER" else T.RAG_RED
        for r in df["rag"]
    ]

    # Marker sizes scaled proportionally by device count (diameter reflects volume)
    max_devs = df["device_count"].max() if not df.empty and df["device_count"].max() > 0 else 1
    sizes = [14 + (count / max_devs) * 36 for count in df["device_count"]]

    hover_texts = [
        f"<b>{row['country_name']}</b><br>"
        f"Region: {row['region']}<br>"
        f"Devices: <b>{row['device_count']}</b> across {row['org_count']} orgs<br>"
        f"Compliance: <b>{row['compliance_score']}%</b> ({row['rag']})<br>"
        f"EOL Devices: {row['eol_count']}"
        for _, row in df.iterrows()
    ]

    fig = go.Figure()

    # Geo scatter points — mode='markers' (shows text ONLY on hover)
    fig.add_trace(
        go.Scattergeo(
            lat=df["lat"],
            lon=df["lon"],
            text=hover_texts,
            hoverinfo="text",
            mode="markers",
            marker=dict(
                size=sizes,
                color=colors,
                line=dict(width=2, color=T.TEXT_PRIMARY),
                opacity=0.88,
            ),
            customdata=df["region"],
        )
    )

    # Geo layout configuration
    geo_config: dict[str, Any] = dict(
        bgcolor=T.BG_CARD,
        showland=True,
        landcolor="#1F242C",
        showocean=True,
        oceancolor=T.BG_PRIMARY,
        showlakes=True,
        lakecolor=T.BG_PRIMARY,
        showcountries=True,
        countrycolor=T.BORDER,
        coastlinecolor=T.BORDER,
        projection_type="natural earth",
        resolution=50,
    )

    # Region focus zoom
    if selected_region == "APAC / Asia":
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

    return _apply_theme(fig, "Global Device Infrastructure & Compliance Map")


# ---------------------------------------------------------------------------
# OS Distribution Charts (2 Separate Donuts: Windows & Linux)
# ---------------------------------------------------------------------------

def windows_os_donut(windows_version_counts: dict[str, int]) -> go.Figure:
    """Donut chart — Granular Windows OS builds breakdown."""
    if not windows_version_counts:
        return _empty_figure("No Windows devices found")

    labels = list(windows_version_counts.keys())
    values = list(windows_version_counts.values())

    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.55,
            marker=dict(line=dict(color=T.BG_PRIMARY, width=2)),
            textinfo="label+percent",
            textfont=dict(color=T.TEXT_PRIMARY, size=10),
            hovertemplate="<b>%{label}</b><br>%{value} Windows devices (%{percent})<extra></extra>",
        )
    )
    fig.update_layout(showlegend=True, height=270)
    return _apply_theme(fig, "Windows OS Builds Breakdown")


def linux_os_donut(linux_version_counts: dict[str, int]) -> go.Figure:
    """Donut chart — Granular Linux distributions breakdown."""
    if not linux_version_counts:
        return _empty_figure("No Linux devices found")

    labels = list(linux_version_counts.keys())
    values = list(linux_version_counts.values())

    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.55,
            marker=dict(line=dict(color=T.BG_PRIMARY, width=2)),
            textinfo="label+percent",
            textfont=dict(color=T.TEXT_PRIMARY, size=10),
            hovertemplate="<b>%{label}</b><br>%{value} Linux systems (%{percent})<extra></extra>",
        )
    )
    fig.update_layout(showlegend=True, height=270)
    return _apply_theme(fig, "Linux Distributions Breakdown")


# ---------------------------------------------------------------------------
# Dedicated End-of-Life (EOL) Charts
# ---------------------------------------------------------------------------

def eol_status_donut(eol_status_counts: dict[str, int]) -> go.Figure:
    """Donut chart — Supported vs Approaching EOL vs Expired."""
    labels = ["Supported", "Approaching EOL", "Expired (EOL)"]
    values = [eol_status_counts.get(l, 0) for l in labels]
    colors = [T.RAG_GREEN, T.RAG_AMBER, T.RAG_RED]

    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.60,
            marker=dict(colors=colors, line=dict(color=T.BG_PRIMARY, width=2)),
            textinfo="label+value",
            textfont=dict(color=T.TEXT_PRIMARY, size=11),
            hovertemplate="<b>%{label}</b><br>%{value} devices (%{percent})<extra></extra>",
        )
    )
    fig.update_layout(showlegend=True, height=240)
    return _apply_theme(fig, "Lifecycle & Support Status")


def eol_by_os_bar(eol_by_os_counts: dict[str, int]) -> go.Figure:
    """Horizontal bar — distribution of devices on obsolete/at-risk OS versions."""
    if not eol_by_os_counts:
        return _empty_figure("✅ No EOL or Approaching-EOL devices found")

    sorted_items = sorted(eol_by_os_counts.items(), key=lambda x: x[1], reverse=True)[:8]
    labels = [i[0] for i in reversed(sorted_items)]
    values = [i[1] for i in reversed(sorted_items)]

    fig = go.Figure(
        go.Bar(
            y=labels,
            x=values,
            orientation="h",
            marker=dict(color=T.RAG_RED, line=dict(color=T.BG_PRIMARY, width=1)),
            hovertemplate="<b>%{y}</b><br>%{x} at-risk devices<extra></extra>",
            text=values,
            textposition="outside",
            textfont=dict(color=T.TEXT_SECONDARY, size=10),
        )
    )
    fig.update_layout(xaxis_title="Affected Devices", yaxis_title="", height=240)
    return _apply_theme(fig, "At-Risk OS Versions")


# ---------------------------------------------------------------------------
# Server / Hosting Charts
# ---------------------------------------------------------------------------

def server_role_bar(role_counts: dict[str, int]) -> go.Figure:
    """Horizontal bar — servers by role."""
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
                line=dict(color=T.BG_PRIMARY, width=1),
            ),
            hovertemplate="<b>%{y}</b><br>%{x} servers<extra></extra>",
            text=values,
            textposition="outside",
            textfont=dict(color=T.TEXT_SECONDARY, size=10),
        )
    )
    fig.update_layout(xaxis_title="Count", yaxis_title="", height=260)
    return _apply_theme(fig, "Server Role Distribution")


def hosting_donut(hosting_counts: dict[str, int], filter_mode: str = "all") -> go.Figure:
    """Donut chart for hosting types supporting filter_mode: 'all', 'onprem', 'cloud'."""
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
        return _empty_figure(f"No devices found for {filter_mode.title()} filter")

    labels = list(filtered_counts.keys())
    values = list(filtered_counts.values())
    colors = [T.HOSTING_COLORS.get(l, T.ACCENT_BLUE) for l in labels]

    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.55,
            marker=dict(colors=colors, line=dict(color=T.BG_PRIMARY, width=2)),
            textinfo="label+percent",
            textfont=dict(color=T.TEXT_PRIMARY, size=11),
            hovertemplate="<b>%{label}</b><br>%{value} devices (%{percent})<extra></extra>",
        )
    )
    fig.update_layout(showlegend=True, height=270)
    return _apply_theme(fig, title)


def hosting_org_stacked_bar(org_distribution: list[dict], filter_mode: str = "all") -> go.Figure:
    """
    Organization-wise stacked bar chart showing device distribution.
    Supports filter_mode: 'all', 'onprem', 'cloud'.
    """
    if not org_distribution:
        return _empty_figure("No organization hosting data available")

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
        xaxis=dict(tickangle=-30, tickfont=dict(size=10, color=T.TEXT_SECONDARY)),
        yaxis=dict(title="Device Count"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return _apply_theme(fig, "Organization-wise Hosting Distribution")


def hosting_role_heatmap(matrix: list[dict]) -> go.Figure:
    """Heatmap — Hosting × Server Role device counts."""
    if not matrix:
        return _empty_figure("No server hosting data available")

    df = pd.DataFrame(matrix)
    pivot = df.pivot_table(index="hosting", columns="role", values="count", fill_value=0)

    fig = go.Figure(
        go.Heatmap(
            z=pivot.values,
            x=pivot.columns.tolist(),
            y=pivot.index.tolist(),
            colorscale=[[0, T.BG_CARD], [0.5, T.ACCENT_BLUE], [1, T.ACCENT_PURPLE]],
            showscale=True,
            hovertemplate="<b>%{y} × %{x}</b><br>%{z} servers<extra></extra>",
            text=pivot.values,
            texttemplate="%{text}",
            textfont=dict(color=T.TEXT_PRIMARY, size=10),
        )
    )
    fig.update_layout(height=220)
    return _apply_theme(fig, "Hosting × Role Matrix")


# ---------------------------------------------------------------------------
# Patch Compliance Gauge (0-60 Red, 61-84 Amber, 85+ Green)
# ---------------------------------------------------------------------------

def patch_gauge(
    patch_pct: float,
    red_limit: float = 60.0,
    amber_limit: float = 84.0,
    green_target: float = 85.0,
) -> go.Figure:
    """
    Speedometer gauge — overall patch coverage %.
    Customizable Thresholds:
      0 to red_limit:        RED
      red_limit to amber_limit: AMBER
      green_target to 100:   GREEN
    """
    color = (
        T.RAG_GREEN if patch_pct >= green_target
        else T.RAG_AMBER if patch_pct >= (red_limit + 1.0)
        else T.RAG_RED
    )

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number+delta",
            value=patch_pct,
            number=dict(suffix="%", font=dict(size=40, color=color)),
            delta=dict(reference=green_target, valueformat=".1f"),
            gauge=dict(
                axis=dict(range=[0, 100], tickcolor=T.TEXT_SECONDARY),
                bar=dict(color=color, thickness=0.25),
                bgcolor=T.BG_PRIMARY,
                bordercolor=T.BORDER,
                steps=[
                    dict(range=[0, red_limit], color="rgba(244,67,54,0.25)"),          # RED
                    dict(range=[red_limit, amber_limit], color="rgba(255,193,7,0.25)"), # AMBER
                    dict(range=[amber_limit, 100], color="rgba(0,200,83,0.25)"),      # GREEN
                ],
                threshold=dict(
                    line=dict(color=T.TEXT_PRIMARY, width=2),
                    thickness=0.75,
                    value=green_target,
                ),
            ),
        )
    )
    fig.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=260)
    return _apply_theme(fig, f"Fleet Patch Coverage (Target: ≥{int(green_target)}%)")


# ---------------------------------------------------------------------------
# Patch SLA Aging & Classification Charts
# ---------------------------------------------------------------------------

def patch_sla_aging_bar(sla_counts: dict[str, int]) -> go.Figure:
    """Bar chart — Distribution of pending patches across SLA aging brackets."""
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
            marker=dict(color=colors, line=dict(color=T.BG_PRIMARY, width=1)),
            hovertemplate="<b>%{x}</b><br>%{y} pending patches<extra></extra>",
            text=values,
            textposition="outside",
            textfont=dict(color=T.TEXT_PRIMARY, size=11, family="Inter, sans-serif"),
        )
    )
    fig.update_layout(xaxis_title="", yaxis_title="Pending Patches", height=250)
    return _apply_theme(fig, "Patch SLA Aging Backlog")


def patch_type_donut(type_counts: dict[str, int]) -> go.Figure:
    """Donut chart — OS Security Patches vs 3rd-Party Applications."""
    labels = list(type_counts.keys())
    values = list(type_counts.values())
    colors = [T.ACCENT_BLUE, T.ACCENT_PURPLE, T.ACCENT_TEAL]

    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.55,
            marker=dict(colors=colors, line=dict(color=T.BG_PRIMARY, width=2)),
            textinfo="label+percent",
            textfont=dict(color=T.TEXT_PRIMARY, size=11),
            hovertemplate="<b>%{label}</b><br>%{value} patches (%{percent})<extra></extra>",
        )
    )
    fig.update_layout(showlegend=True, height=250)
    return _apply_theme(fig, "Patch Category Breakdown")


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _empty_figure(message: str = "No data") -> go.Figure:
    """Placeholder figure shown when data is absent."""
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        showarrow=False,
        font=dict(color=T.TEXT_MUTED, size=13),
    )
    fig.update_layout(xaxis=dict(visible=False), yaxis=dict(visible=False), height=220)
    return _apply_theme(fig)
