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
        assert "NinjaOne IT Infrastructure & Compliance Executive Audit" in html_out
        assert "Total Endpoints" in html_out
        assert "Organization Compliance Scorecard" in html_out
        assert "End-of-Life (EOL) Device Ledger" not in html_out
        assert "plotly" in html_out.lower()

    def test_html_report_custom_amber_threshold(self):
        """User requirement: saving compliance threshold to 90% for amber in Settings must reflect in HTML export."""
        data = get_mock_dashboard_data(patch_red=60.0, patch_amber=90.0, patch_green=92.0)
        html_out = generate_html_report(data)

        # Gauge steps reflect amber step to 90% and target 92%
        assert "92%" in html_out
        assert "90.0" in html_out or "90%" in html_out
        # KPI card subtitle reflects user's custom target and amber threshold
        assert "Fleet SLA Target &ge;92% (Amber &le;90%)" in html_out

    def test_html_report_patch_type_scope(self):
        """Verify that patch_type slicer displays properly in HTML report scope."""
        data_os = get_mock_dashboard_data(active_patch_type="os")
        html_os = generate_html_report(data_os)
        assert "Patches: OS" in html_os

        data_sw = get_mock_dashboard_data(active_patch_type="software")
        html_sw = generate_html_report(data_sw)
        assert "Patches: SOFTWARE" in html_sw
