"""Tests for Standalone Interactive HTML Report Generator."""

import pytest
from scripts.generate_sample_data import get_mock_dashboard_data
from src.reporting.html_export import generate_html_report


class TestHTMLExport:
    def test_generate_html_report(self):
        data = get_mock_dashboard_data()
        html_out = generate_html_report(data)

        assert isinstance(html_out, str)
        assert len(html_out) > 5000
        assert "<!DOCTYPE html>" in html_out
        assert "NinjaOne IT Infrastructure" in html_out
        assert "Executive Dashboard" in html_out
        assert "Total Endpoints" in html_out
        assert "Organization Compliance Scorecard" in html_out
        assert "End-of-Life (EOL) Device Ledger" not in html_out
        assert "plotly" in html_out.lower()

        # Verify Tabbed Structure
        assert 'id="tab-btn-exec"' in html_out
        assert 'id="tab-btn-ops"' in html_out
        assert 'id="tab-view-exec"' in html_out
        assert 'id="tab-view-ops"' in html_out
        assert "switchDashboardTab" in html_out

        # Verify Theme Switcher & Table Search
        assert 'id="theme-toggle-btn"' in html_out
        assert "toggleTheme()" in html_out
        assert "filterTable(" in html_out

    def test_html_report_custom_amber_threshold(self):
        """User requirement: saving compliance threshold to 90% for amber in Settings must reflect in HTML export."""
        data = get_mock_dashboard_data(patch_red=60.0, patch_amber=90.0, patch_green=92.0)
        html_out = generate_html_report(data)

        # Gauge steps reflect amber step to 90% and target 92%
        assert "92%" in html_out
        assert "90.0" in html_out or "90%" in html_out
        assert "Fleet SLA Target &ge;92%" in html_out

    def test_html_report_patch_type_scope(self):
        """Verify that patch_type slicer displays properly in HTML report scope."""
        data_os = get_mock_dashboard_data(active_patch_type="os")
        html_os = generate_html_report(data_os)
        assert "Patches: OS" in html_os

        data_sw = get_mock_dashboard_data(active_patch_type="software")
        html_sw = generate_html_report(data_sw)
        assert "Patches: SOFTWARE" in html_sw

    def test_html_report_light_and_dark_theme(self):
        """Verify that HTML export adapts to light and dark theme mode and supports client-side theme switching."""
        data = get_mock_dashboard_data()

        # Light theme default
        html_light = generate_html_report(data, theme_mode="light")
        assert 'data-theme="light"' in html_light
        assert "--bg-primary: #F8FAFC;" in html_light
        assert "--text-primary: #0F172A;" in html_light

        # Dark theme default
        html_dark = generate_html_report(data, theme_mode="dark")
        assert 'data-theme="dark"' in html_dark
        assert "--bg-primary: #0D1117;" in html_dark
        assert "--text-primary: #E6EDF3;" in html_dark

    def test_html_report_patch_operations_details(self):
        """Verify that HTML export renders all 3 patch operations details tables in Tab 2."""
        data = get_mock_dashboard_data()
        html_out = generate_html_report(data)

        assert "Top 10 Servers with Max Pending Patches" in html_out
        assert "Top 10 Patches Pending on Max Servers" in html_out
        assert "Patch Deployment Failure Triage" in html_out
        assert "Patch Category Breakdown" in html_out
        assert 'id="top-servers-table"' in html_out
        assert 'id="top-patches-table"' in html_out
        assert 'id="failures-table"' in html_out
