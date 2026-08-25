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
