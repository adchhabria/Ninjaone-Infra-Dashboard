"""Unit test for PDF report generation."""
import pytest
from scripts.generate_sample_data import get_mock_dashboard_data
from src.metrics.pdf_export import generate_pdf_report

class TestPDFExport:
    def test_generate_pdf_report_bytes(self):
        data = get_mock_dashboard_data()
        pdf_bytes = generate_pdf_report(data)
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 1000
        assert pdf_bytes.startswith(b"%PDF")

    def test_generate_pdf_report_themes(self):
        data = get_mock_dashboard_data()
        # Light theme PDF
        pdf_light = generate_pdf_report(data, theme_mode="light")
        assert isinstance(pdf_light, bytes)
        assert len(pdf_light) > 1000
        assert pdf_light.startswith(b"%PDF")

        # Dark theme PDF
        pdf_dark = generate_pdf_report(data, theme_mode="dark")
        assert isinstance(pdf_dark, bytes)
        assert len(pdf_dark) > 1000
        assert pdf_dark.startswith(b"%PDF")
