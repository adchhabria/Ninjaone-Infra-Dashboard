"""
Unit tests for Selective Patch Compliance and Browser Heartbeat / Auto-Shutdown.
"""

import time
import pytest
from src.api.models import Device, OSInfo
from src.api.patches import is_os_security_or_cumulative_patch
from src.metrics.patch_compliance import (
    get_device_os_security_patch_info,
    compute_patch_metrics,
)
from src.dashboard.app import BrowserWatchdog, create_app


def test_is_os_security_or_cumulative_patch_selective():
    """Verify that when selected_patch_titles is specified, ONLY matching patches return True."""
    sel = ["KB5127648", "2024-10 Cumulative Update for Windows Server 2022 (KB5044281)"]

    # Exact or substring KB matches
    assert is_os_security_or_cumulative_patch("2024-05 Cumulative Update for Windows (KB5127648)", selected_patch_titles=sel) is True
    assert is_os_security_or_cumulative_patch("Security Update KB5127648", selected_patch_titles=sel) is True
    assert is_os_security_or_cumulative_patch("2024-10 Cumulative Update for Windows Server 2022 (KB5044281)", selected_patch_titles=sel) is True

    # Non-selected patches MUST return False in selective mode, even if they have "Cumulative Update" or "Security Update"
    assert is_os_security_or_cumulative_patch("2024-06 Cumulative Update (KB9999999)", selected_patch_titles=sel) is False
    assert is_os_security_or_cumulative_patch("Security Update for Windows 10 (KB1234567)", selected_patch_titles=sel) is False


def test_selective_device_compliance():
    """
    Test compliance evaluation:
    - Server 1 has KB5127648 pending -> Non-Compliant when KB5127648 is selected
    - Server 2 has KB9999999 and software pending (but NOT KB5127648) -> Compliant when KB5127648 is selected
    - Server 3 has no pending patches -> Compliant
    """
    s1 = Device(
        id=1,
        organizationId=101,
        systemName="SRV-PROD-01",
        os=OSInfo(name="Windows Server 2022"),
        all_uninstalled_patch_names=["2024-05 Security Update (KB5127648)"],
    )
    s2 = Device(
        id=2,
        organizationId=101,
        systemName="SRV-PROD-02",
        os=OSInfo(name="Windows Server 2022"),
        all_uninstalled_patch_names=["2024-09 Cumulative Update (KB9999999)"],
        approved_software_count=4,
    )
    s3 = Device(
        id=3,
        organizationId=102,
        systemName="SRV-PROD-03",
        os=OSInfo(name="Windows Server 2019"),
        all_uninstalled_patch_names=[],
    )

    # In selective mode for KB5127648:
    info1_cnt, info1_names = get_device_os_security_patch_info(s1, selected_patch_titles=["KB5127648"])
    assert info1_cnt == 1
    assert "KB5127648" in info1_names[0]

    info2_cnt, info2_names = get_device_os_security_patch_info(s2, selected_patch_titles=["KB5127648"])
    assert info2_cnt == 0
    assert info2_names == []

    info3_cnt, info3_names = get_device_os_security_patch_info(s3, selected_patch_titles=["KB5127648"])
    assert info3_cnt == 0
    assert info3_names == []

    # Full fleet calculation
    res = compute_patch_metrics(
        devices=[s1, s2, s3],
        selected_patch_titles=["KB5127648"],
    )

    # Out of 3 servers: 1 non-compliant (missing KB5127648), 2 compliant (have it installed / not pending)
    assert res["compliant_count"] == 2
    assert res["non_compliant_count"] == 1
    assert round(res["patch_coverage_pct"], 1) == 66.7

    # Check server table entries
    tbl = res["server_compliance_table"]
    srv1_row = next(r for r in tbl if r["device_id"] == 1)
    srv2_row = next(r for r in tbl if r["device_id"] == 2)
    srv3_row = next(r for r in tbl if r["device_id"] == 3)

    assert srv1_row["is_compliant"] is False
    assert srv1_row["status"] == "Non-Compliant"
    assert "KB5127648" in srv1_row["pending_security_patches_str"]

    assert srv2_row["is_compliant"] is True
    assert srv2_row["status"] == "Compliant"
    assert "Compliant" in srv2_row["pending_security_patches_str"]

    assert srv3_row["is_compliant"] is True
    assert srv3_row["status"] == "Compliant"


def test_browser_heartbeat_endpoints():
    """Verify heartbeat and heartbeat-close endpoints return 200 OK and record pings."""
    app = create_app()
    client = app.server.test_client()

    resp_ping = client.post("/api/heartbeat")
    assert resp_ping.status_code == 200
    assert b"OK" in resp_ping.data

    resp_close = client.post("/api/heartbeat-close")
    assert resp_close.status_code == 200
    assert b"OK" in resp_close.data


def test_browser_watchdog_logic():
    """Verify watchdog state transitions."""
    wd = BrowserWatchdog(timeout_sec=5.0, startup_grace_sec=10.0)
    assert wd.has_connected is False
    assert wd.last_heartbeat == 0.0

    wd.ping()
    assert wd.has_connected is True
    assert wd.last_heartbeat > 0.0

    wd.mark_unload()
    assert wd.unload_requested_at > 0.0

    # A reconnect resets unload_requested_at
    wd.ping()
    assert wd.unload_requested_at == 0.0
