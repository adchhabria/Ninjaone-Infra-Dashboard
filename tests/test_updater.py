"""
Unit tests for the Auto-Updater and Version Management Engine.
"""

from unittest.mock import MagicMock, patch
import pytest

from src.utils.updater import (
    CURRENT_VERSION,
    check_for_updates,
    is_newer_version,
    normalize_version,
)


class TestUpdater:
    def test_normalize_version(self):
        assert normalize_version("v1.0.0") == "1.0.0"
        assert normalize_version("V2.3.4") == "2.3.4"
        assert normalize_version("  1.2.0  ") == "1.2.0"
        assert normalize_version("v1.5-beta") == "1.5"

    def test_is_newer_version(self):
        assert is_newer_version("1.1.0", "1.0.0") is True
        assert is_newer_version("2.0.0", "1.9.9") is True
        assert is_newer_version("1.0.1", "1.0.0") is True
        assert is_newer_version("1.0.0", "1.0.0") is False
        assert is_newer_version("0.9.9", "1.0.0") is False
        assert is_newer_version("v1.2.0", "v1.0.0") is True

    @patch("urllib.request.urlopen")
    def test_check_for_updates_available(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b"""{
            "tag_name": "v1.2.0",
            "name": "Release v1.2.0 - Security Patches",
            "body": "Added new vulnerability audit capabilities.",
            "published_at": "2026-09-01T12:00:00Z",
            "html_url": "https://github.com/adchhabria/Ninjaone-Infra-Dashboard/releases/tag/v1.2.0",
            "assets": [
                {
                    "name": "Ninjaone-Infra-Dashboard.exe",
                    "browser_download_url": "https://github.com/adchhabria/Ninjaone-Infra-Dashboard/releases/download/v1.2.0/Ninjaone-Infra-Dashboard.exe"
                }
            ]
        }"""
        mock_urlopen.return_value.__enter__.return_value = mock_response

        res = check_for_updates()
        assert res["success"] is True
        assert res["update_available"] is True
        assert res["latest_version"] == "v1.2.0"
        assert "Ninjaone-Infra-Dashboard.exe" in res["download_url"]

    @patch("urllib.request.urlopen")
    def test_check_for_updates_already_latest(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = f"""{{
            "tag_name": "v{CURRENT_VERSION}",
            "name": "Latest Release",
            "body": "Current production release.",
            "published_at": "2026-09-17T12:00:00Z",
            "html_url": "https://github.com/adchhabria/Ninjaone-Infra-Dashboard/releases/tag/v{CURRENT_VERSION}",
            "assets": []
        }}""".encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        res = check_for_updates()
        assert res["success"] is True
        assert res["update_available"] is False
        assert res["latest_version"] == f"v{CURRENT_VERSION}"

    def test_update_state_management(self):
        from src.utils.updater import get_update_state, reset_update_state, _set_update_state

        reset_update_state()
        state = get_update_state()
        assert state["status"] == "idle"
        assert state["progress"] == 0

        _set_update_state(status="downloading", progress=45, downloaded_mb=12.5, total_mb=25.0)
        state2 = get_update_state()
        assert state2["status"] == "downloading"
        assert state2["progress"] == 45
        assert state2["downloaded_mb"] == 12.5

        reset_update_state()
        assert get_update_state()["status"] == "idle"

    def test_start_auto_update_empty_url(self):
        from src.utils.updater import start_auto_update
        ok, msg = start_auto_update("")
        assert ok is False
        assert "No download URL" in msg

    @patch("threading.Thread")
    def test_start_auto_update_valid_url(self, mock_thread):
        from src.utils.updater import start_auto_update, reset_update_state
        reset_update_state()
        ok, msg = start_auto_update("https://github.com/fake/url.exe")
        assert ok is True
        mock_thread.return_value.start.assert_called_once()
        reset_update_state()


