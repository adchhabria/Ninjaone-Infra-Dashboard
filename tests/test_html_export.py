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
        assert "plotly" in html_out.lower()
