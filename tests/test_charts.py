"""Tests for updated Plotly chart builder functions."""

from datetime import date
import pytest
import plotly.graph_objects as go

from src.dashboard.charts import (
    windows_os_donut,
    linux_os_donut,
    server_role_bar,
    hosting_donut,
    hosting_role_heatmap,
    patch_gauge,
    patch_compliance_ytd_trend_line,
    DEFAULT_YTD_TREND,
    get_patch_cycle_current_month,
    get_patch_cycle_12_months,
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
        # Verify 5-point meter bar tick division instead of 20 points
        assert fig_green.data[0].gauge.axis.dtick == 5
        # Verify title is strictly "Current month patch compliance"
        assert fig_green.layout.title.text == "Current month patch compliance"
        # Verify solid, vibrant RAG colors
        steps = fig_green.data[0].gauge.steps
        assert steps[0].color == "#DC2626"
        assert steps[1].color == "#F59E0B"
        assert steps[2].color == "#16A34A"
        fig_amber = patch_gauge(75.0)
        assert isinstance(fig_amber, go.Figure)
        fig_red = patch_gauge(55.0)
        assert isinstance(fig_red, go.Figure)

    def test_patching_cycle_rules(self):
        # With today's date N-1 rule: Any day in November 2026 (Nov 10 or Nov 2) has current cycle as Oct-26 (N-1)
        cycle_year, cycle_month = get_patch_cycle_current_month(date(2026, 11, 10))
        assert (cycle_year, cycle_month) == (2026, 10)
        months_nov10 = get_patch_cycle_12_months(date(2026, 11, 10))
        assert len(months_nov10) == 12
        assert months_nov10[-1] == "Oct-26"
        assert months_nov10[0] == "Nov-25"

        # On Nov 2, 2026, current cycle is also Oct-26 (N-1) rolling back 12 months to Nov-25
        cycle_year_pre, cycle_month_pre = get_patch_cycle_current_month(date(2026, 11, 2))
        assert (cycle_year_pre, cycle_month_pre) == (2026, 10)
        months_nov2 = get_patch_cycle_12_months(date(2026, 11, 2))
        assert len(months_nov2) == 12
        assert months_nov2[-1] == "Oct-26"
        assert months_nov2[0] == "Nov-25"

        # On Jan 15, 2026, current cycle is Dec-25 (N-1) rolling back to Jan-25
        cycle_year_jan, cycle_month_jan = get_patch_cycle_current_month(date(2026, 1, 15))
        assert (cycle_year_jan, cycle_month_jan) == (2025, 12)
        months_jan = get_patch_cycle_12_months(date(2026, 1, 15))
        assert months_jan[-1] == "Dec-25"
        assert months_jan[0] == "Jan-25"

    def test_patch_compliance_ytd_trend_line(self):
        # Default 12-month data aligned to active cycle (ref_date in Nov 2026 -> ends in Oct-26)
        fig_default = patch_compliance_ytd_trend_line(ref_date=date(2026, 11, 5))
        assert isinstance(fig_default, go.Figure)
        assert len(fig_default.data) == 2  # Target line + Compliance trend
        assert len(fig_default.data[1].x) == 12
        assert fig_default.data[1].x[-1] == "Oct-26"
        assert fig_default.data[1].x[0] == "Nov-25"

        # Custom user data
        custom_data = {
            "Nov-25": 80, "Dec-25": 82, "Jan-26": 90, "Feb-26": 85,
            "Mar-26": 88, "Apr-26": 74, "May-26": 95, "Jun-26": 90,
            "Jul-26": 50, "Aug-26": 70, "Sep-26": 85, "Oct-26": 96,
        }
        fig_custom = patch_compliance_ytd_trend_line(custom_data, theme_mode="light", ref_date=date(2026, 11, 5))
        assert isinstance(fig_custom, go.Figure)
        assert list(fig_custom.data[1].y) == [80, 82, 90, 85, 88, 74, 95, 90, 50, 70, 85, 96]

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
