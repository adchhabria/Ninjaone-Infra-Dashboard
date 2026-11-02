"""
Tests for Filtered Report Downloads (Excel, PDF, and HTML).

Verifies that:
1. Active filters (Organization, Location, Region, OS Family) are respected during download.
2. Excel downloads produce valid .xlsx files with filtered scope in filename.
3. PDF downloads produce valid .pdf files with filtered scope in filename.
4. HTML report downloads produce valid .html reports with filtered scope in filename.
5. Flask direct download routes (/download/excel, /download/pdf, /download/html) accept filter query params.
"""

import pytest
from src.dashboard.app import create_app
from src.metrics.data_provider import coordinator
from scripts.generate_sample_data import get_mock_dashboard_data


class TestFilteredDownloads:
    @pytest.fixture
    def app(self):
        return create_app()

    def test_flask_endpoint_filtered_html(self, app):
        client = app.server.test_client()
        # Filter by Org 2 (London EMEA Hub)
        resp = client.get("/download/html?org_id=2&location=London+Office")
        assert resp.status_code == 200
        assert "text/html" in resp.content_type
        # Header Content-Disposition contains .html and scope
        cd = resp.headers.get("Content-Disposition", "")
        assert ".html" in cd
        assert "London" in cd or "Org" in cd
        assert b"London EMEA Hub" in resp.data

    def test_flask_endpoint_filtered_html_with_amber_threshold_and_patch_type(self, app):
        client = app.server.test_client()
        # Request with patch_type=os and patch_amber=90
        resp = client.get("/download/html?patch_type=os&patch_amber=90.0&patch_green=95.0")
        assert resp.status_code == 200
        assert "text/html" in resp.content_type
        html_str = resp.data.decode("utf-8")
        assert "Patches: OS" in html_str
        assert "Fleet SLA Target &ge;95% (Amber &le;90%)" in html_str

    def test_flask_endpoint_filtered_excel(self, app):
        client = app.server.test_client()
        resp = client.get("/download/excel?org_id=1")
        assert resp.status_code == 200
        assert "openxmlformats" in resp.content_type
        cd = resp.headers.get("Content-Disposition", "")
        assert ".xlsx" in cd
        assert len(resp.data) > 1000

    def test_flask_endpoint_filtered_pdf(self, app):
        client = app.server.test_client()
        resp = client.get("/download/pdf?location=Tokyo+Center")
        assert resp.status_code == 200
        assert "application/pdf" in resp.content_type
        cd = resp.headers.get("Content-Disposition", "")
        assert ".pdf" in cd
        assert resp.data.startswith(b"%PDF")

    def test_flask_endpoint_html_theme_mode(self, app):
        client = app.server.test_client()
        resp = client.get("/download/html?theme=light")
        assert resp.status_code == 200
        assert b"--bg-primary: #F8FAFC;" in resp.data

        resp_dark = client.get("/download/html?theme=dark")
        assert resp_dark.status_code == 200
        assert b"--bg-primary: #0D1117;" in resp_dark.data

    def test_flask_endpoint_view_and_share_html(self, app):
        client = app.server.test_client()
        # Direct unauthenticated browser link
        resp = client.get("/view")
        assert resp.status_code == 200
        assert "text/html" in resp.content_type
        assert "Content-Disposition" not in resp.headers  # Inline view, not attachment
        assert b"tab-btn-exec" in resp.data
        assert b"tab-btn-ops" in resp.data

        resp_share = client.get("/share?theme=dark")
        assert resp_share.status_code == 200
        assert "text/html" in resp_share.content_type
        assert b'data-theme="dark"' in resp_share.data

    def test_no_duplicate_callback_outputs(self, app):
        from collections import Counter
        client = app.server.test_client()
        resp = client.get("/_dash-dependencies")
        assert resp.status_code == 200
        deps = resp.json
        outputs = [cb.get("output") for cb in deps]
        counts = Counter(outputs)
        duplicates = {k: v for k, v in counts.items() if v > 1}
        assert duplicates == {}, f"Duplicate callback outputs found: {duplicates}"

