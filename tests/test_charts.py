"""Tests for updated Plotly chart builder functions."""

import pytest
import plotly.graph_objects as go

from src.dashboard.charts import (
    windows_os_donut,
    linux_os_donut,
    server_role_bar,
    hosting_donut,
    hosting_role_heatmap,
    patch_gauge,
    world_map_chart,
    eol_status_donut,
    eol_by_os_bar,
    patch_sla_aging_bar,
    patch_type_donut,
    _empty_figure,
)


class TestCharts:
    """All chart builders should return valid go.Figure objects."""

    def test_windows_os_donut(self):
        fig = windows_os_donut({"Windows 11 23H2": 80, "Windows 10 22H2": 60})
        assert isinstance(fig, go.Figure)

    def test_linux_os_donut(self):
        fig = linux_os_donut({"Ubuntu 22.04 LTS": 30, "CentOS 7": 10})
        assert isinstance(fig, go.Figure)

    def test_server_role_bar(self):
        fig = server_role_bar({"Domain Controller": 3, "File Server": 5})
        assert isinstance(fig, go.Figure)

    def test_hosting_donut(self):
        fig = hosting_donut({"AWS": 15, "Azure": 20, "GCP": 5, "Physical Hardware": 25, "Virtual Machines (VMs)": 30})
        assert isinstance(fig, go.Figure)

    def test_patch_gauge(self):
        fig_green = patch_gauge(88.0)
        assert isinstance(fig_green, go.Figure)
        fig_amber = patch_gauge(75.0)
        assert isinstance(fig_amber, go.Figure)
        fig_red = patch_gauge(55.0)
        assert isinstance(fig_red, go.Figure)

    def test_world_map_chart_hover_only(self):
        map_data = [
            {"country_code": "USA", "country_name": "United States", "region": "USA / North America", "lat": 37.09, "lon": -95.71, "device_count": 100, "org_count": 2, "compliance_score": 92.0, "rag": "GREEN", "eol_count": 2},
        ]
        fig = world_map_chart(map_data, selected_region="USA / North America")
        assert isinstance(fig, go.Figure)
        # Check mode is 'markers' so text is hover only
        assert fig.data[0].mode == "markers"

    def test_eol_status_donut(self):
        counts = {"Supported": 180, "Approaching EOL": 20, "Expired (EOL)": 15}
        fig = eol_status_donut(counts)
        assert isinstance(fig, go.Figure)

    def test_eol_by_os_bar(self):
        by_os = {"Windows 8.1": 8, "CentOS 7": 4}
        fig = eol_by_os_bar(by_os)
        assert isinstance(fig, go.Figure)

    def test_patch_sla_aging_bar(self):
        counts = {"< 7 Days (Within SLA)": 40, "8 - 30 Days (Warning)": 15, "31 - 90 Days (High Risk)": 8, "> 90 Days (SLA Breach)": 3}
        fig = patch_sla_aging_bar(counts)
        assert isinstance(fig, go.Figure)

    def test_patch_type_donut(self):
        counts = {"OS Security Updates": 50, "3rd-Party Applications": 30}
        fig = patch_type_donut(counts)
        assert isinstance(fig, go.Figure)
