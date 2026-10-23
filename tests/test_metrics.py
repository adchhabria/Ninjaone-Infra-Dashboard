"""Tests for updated metrics computation modules."""

import pytest
from datetime import datetime, timezone

from src.api.models import Device, OSInfo, Organization
from src.metrics.os_compliance import compute_os_metrics, _is_eol, _get_eol_info, _classify_os_family
from src.metrics.server_hosting import compute_server_metrics, _is_server
from src.metrics.patch_compliance import compute_patch_metrics
from src.metrics.aggregator import resolve_geo, compute_dashboard_slice


def make_device(
    device_id: int = 1,
    org_id: int = 1,
    os_name: str = "Windows 11 23H2",
    release_id: str | None = "23H2",
    node_class: str = "WINDOWS_WORKSTATION",
    offline: bool = False,
    region: str = "USA / North America",
    country: str = "USA",
    location_name: str = "New York HQ",
    hosting_type: str | None = None,
    custom_fields: dict | None = None,
) -> Device:
    return Device(
        id=device_id,
        organizationId=org_id,
        nodeClass=node_class,
        offline=offline,
        displayName=f"PC-{device_id}",
        region=region,
        country=country,
        location_name=location_name,
        hosting_type=hosting_type,
        os=OSInfo(name=os_name, releaseId=release_id),
        custom_fields=custom_fields or {},
    )


class TestOSCompliance:
    def test_eol_detection_windows_8(self):
        info = _get_eol_info("Windows 8.1 Pro")
        assert info["is_eol"] is True
        assert info["status"] == "Expired (EOL)"
        assert info["days_overdue"] > 0
        assert info["risk_level"] in ["CRITICAL", "HIGH"]

    def test_non_eol_windows_11(self):
        info = _get_eol_info("Windows 11 23H2")
        assert info["is_eol"] is False
        assert info["status"] == "Supported"

    def test_approaching_eol(self):
        info = _get_eol_info("Windows Server 2016")
        assert info["is_eol"] is False

    def test_compute_os_metrics_empty(self):
        result = compute_os_metrics([])
        assert result["os_compliance_pct"] == 100.0
        assert result["total_devices"] == 0

    def test_compute_os_metrics_with_eol(self):
        devices = [
            make_device(1, os_name="Windows 11 23H2"),
            make_device(2, os_name="Windows 8.1 Pro"),     # EOL
            make_device(3, os_name="Ubuntu 22.04 LTS"),
        ]
        result = compute_os_metrics(devices)
        assert result["eol_count"] == 1
        assert len(result["eol_table_data"]) == 1
        assert result["eol_status_counts"]["Expired (EOL)"] == 1
        assert result["eol_status_counts"]["Supported"] == 2
        assert len(result["windows_version_counts"]) > 0
        assert len(result["linux_version_counts"]) > 0


class TestServerHosting:
    def test_server_hosting_multi_cloud(self):
        devices = [
            make_device(1, node_class="WINDOWS_SERVER", hosting_type="AWS"),
            make_device(2, node_class="WINDOWS_SERVER", hosting_type="Azure"),
            make_device(3, node_class="LINUX_SERVER", hosting_type="GCP"),
            make_device(4, node_class="LINUX_SERVER", hosting_type="Virtual Machines (VMs)"),
            make_device(5, node_class="WINDOWS_SERVER", hosting_type="Physical Hardware"),
        ]
        result = compute_server_metrics(devices)
        assert result["server_count"] == 5
        assert result["hosting_counts"]["AWS"] == 1
        assert result["hosting_counts"]["Azure"] == 1
        assert result["hosting_counts"]["GCP"] == 1
        assert result["hosting_counts"]["Virtual Machines (VMs)"] == 1
        assert result["hosting_counts"]["Physical Hardware"] == 1


class TestDashboardSliceFiltering:
    def test_filter_by_location(self):
        org1 = Organization(id=1, name="US Org", region="USA / North America", country="USA")
        dev1 = make_device(1, org_id=1, location_name="New York HQ")
        dev2 = make_device(2, org_id=1, location_name="London Office")

        slice_data = compute_dashboard_slice(
            devices=[dev1, dev2],
            organizations=[org1],
            activities=[],
            active_location="London Office",
        )
        assert slice_data.total_devices == 1

    def test_filter_by_os_family(self):
        org1 = Organization(id=1, name="US Org", region="USA / North America", country="USA")
        dev1 = make_device(1, org_id=1, os_name="Windows 11 23H2")
        dev2 = make_device(2, org_id=1, os_name="Ubuntu 22.04 LTS")

        slice_data = compute_dashboard_slice(
            devices=[dev1, dev2],
            organizations=[org1],
            activities=[],
            active_os_family="Linux",
        )
        assert slice_data.total_devices == 1


class TestServerComplianceAndCustomEOL:
    def test_server_patch_and_software_compliance(self):
        from src.metrics.patch_compliance import compute_patch_metrics

        s1 = Device(
            id=101,
            organizationId=1,
            nodeClass="WINDOWS_SERVER",
            displayName="SRV-PROD-01",
            approved_patch_count=0,
            approved_software_count=2,
            os=OSInfo(name="Windows Server 2022 Standard"),
        )
        s2 = Device(
            id=102,
            organizationId=1,
            nodeClass="WINDOWS_SERVER",
            displayName="SRV-PROD-02",
            approved_patch_count=3,
            approved_software_count=0,
            os=OSInfo(name="Windows Server 2022 Standard"),
        )

        # A. OS patches only
        res_os = compute_patch_metrics([s1, s2], org_name_map={1: "Acme Corp"}, patch_type="os")
        assert res_os["compliant_count"] == 1
        assert res_os["non_compliant_count"] == 1
        assert res_os["patch_coverage_pct"] == 50.0

        table_os = res_os["server_compliance_table"]
        srv1_os = next(r for r in table_os if r["device_id"] == 101)
        assert srv1_os["approved_patch_count"] == 0
        assert srv1_os["approved_software_count"] == 2
        assert srv1_os["effective_patch_count"] == 0
        assert srv1_os["status"] == "Compliant"
        assert srv1_os["is_compliant"] is True

        srv2_os = next(r for r in table_os if r["device_id"] == 102)
        assert srv2_os["approved_patch_count"] == 3
        assert srv2_os["effective_patch_count"] == 3
        assert srv2_os["status"] == "Non-Compliant"
        assert srv2_os["is_compliant"] is False

        # B. Software patches only
        res_sw = compute_patch_metrics([s1, s2], org_name_map={1: "Acme Corp"}, patch_type="software")
        assert res_sw["compliant_count"] == 1
        assert res_sw["non_compliant_count"] == 1
        table_sw = res_sw["server_compliance_table"]
        srv1_sw = next(r for r in table_sw if r["device_id"] == 101)
        assert srv1_sw["effective_patch_count"] == 2
        assert srv1_sw["status"] == "Non-Compliant"
        srv2_sw = next(r for r in table_sw if r["device_id"] == 102)
        assert srv2_sw["effective_patch_count"] == 0
        assert srv2_sw["status"] == "Compliant"

        # C. Both (OS + Software)
        res_both = compute_patch_metrics([s1, s2], org_name_map={1: "Acme Corp"}, patch_type="both")
        assert res_both["compliant_count"] == 0
        assert res_both["non_compliant_count"] == 2
        assert res_both["patch_coverage_pct"] == 0.0

    def test_server_compliance_os_cumulative_and_security_updates(self):
        """
        Verify that a server with uninstalled approved updates is ONLY Non-Compliant
        if the update is an OS Cumulative Update or OS Security Update.
        Updates for .NET, MS Office, SQL Server, and drivers do NOT mark the server Non-Compliant.
        """
        # Server A: Has 3 pending updates, but ALL are .NET or Drivers -> Must be COMPLIANT!
        server_a = Device(
            id=201,
            organizationId=1,
            nodeClass="WINDOWS_SERVER",
            displayName="SRV-DOTNET-01",
            approved_patch_count=3,
            os_security_patch_count=0,
            os_security_patch_names=[
                "2024-10 Cumulative Update for .NET Framework 3.5 and 4.8.1 (KB5044091)",
                "Security Update for SQL Server 2019 (KB5014353)",
                "Intel Network Adapter Driver Update",
            ],
            os=OSInfo(name="Windows Server 2022 Datacenter"),
        )

        # Server B: Has 1 pending update, which is an OS Cumulative Update -> Must be NON-COMPLIANT!
        server_b = Device(
            id=202,
            organizationId=1,
            nodeClass="WINDOWS_SERVER",
            displayName="SRV-WIN-02",
            approved_patch_count=1,
            os_security_patch_count=1,
            os_security_patch_names=[
                "2024-10 Cumulative Update for Windows Server 2022 for x64-based Systems (KB5044281)",
            ],
            os=OSInfo(name="Windows Server 2022 Datacenter"),
        )

        # Server C: Has 0 pending updates -> Must be COMPLIANT!
        server_c = Device(
            id=203,
            organizationId=1,
            nodeClass="WINDOWS_SERVER",
            displayName="SRV-CLEAN-03",
            approved_patch_count=0,
            os_security_patch_count=0,
            os_security_patch_names=[],
            os=OSInfo(name="Windows Server 2022 Datacenter"),
        )

        res = compute_patch_metrics([server_a, server_b, server_c], org_name_map={1: "Acme Corp"}, patch_type="os")
        assert res["total_devices"] == 3
        assert res["compliant_count"] == 2  # Servers A and C are Compliant
        assert res["non_compliant_count"] == 1  # Server B is Non-Compliant
        assert res["patch_coverage_pct"] == 66.7

        tbl = res["server_compliance_table"]
        row_a = next(r for r in tbl if r["device_id"] == 201)
        assert row_a["status"] == "Compliant"
        assert row_a["is_compliant"] is True
        assert row_a["os_security_patch_count"] == 0

        row_b = next(r for r in tbl if r["device_id"] == 202)
        assert row_b["status"] == "Non-Compliant"
        assert row_b["is_compliant"] is False
        assert row_b["os_security_patch_count"] == 1
        assert "KB5044281" in row_b["pending_security_patches_str"]

        row_c = next(r for r in tbl if r["device_id"] == 203)
        assert row_c["status"] == "Compliant"
        assert row_c["is_compliant"] is True

    def test_custom_eol_date_mm_dd_yyyy_calculation(self):
        from src.metrics.os_compliance import _get_eol_info, compute_os_metrics

        # Setting Windows Server 2022 to a past date in MM/DD/YYYY format
        custom = {"Windows Server 2022": "01/15/2023"}
        info = _get_eol_info("Windows Server 2022 Datacenter", custom_eol_dates=custom)
        assert info["is_eol"] is True
        assert info["status"] == "Expired (EOL)"
        assert info["days_overdue"] > 0

        # Setting Windows Server 2022 to a future date in MM/DD/YYYY format
        custom_future = {"Windows Server 2022": "10/14/2035"}
        info_future = _get_eol_info("Windows Server 2022 Datacenter", custom_eol_dates=custom_future)
        assert info_future["is_eol"] is False
        assert info_future["status"] == "Supported"

    def test_live_fleet_compliance_calculation_with_1029_non_compliant_of_1704(self):
        # User scenario: 1029 non-compliant out of 1704 devices
        devices = []
        for i in range(1, 676):
            devices.append(Device(
                id=i,
                organizationId=1,
                nodeClass="WINDOWS_SERVER",
                displayName=f"SRV-{i}",
                approved_patch_count=0,
            ))
        for i in range(676, 1705):
            devices.append(Device(
                id=i,
                organizationId=1,
                nodeClass="WINDOWS_SERVER",
                displayName=f"SRV-{i}",
                approved_patch_count=1 + (i % 5),
            ))

        assert len(devices) == 1704
        res = compute_patch_metrics(devices)
        assert res["total_devices"] == 1704
        assert res["compliant_count"] == 675
        assert res["non_compliant_count"] == 1029
        assert res["patch_coverage_pct"] == 39.6
        assert res["patch_coverage_pct"] < 50.0

    def test_ttl_cache_disk_persistence(self, tmp_path, monkeypatch):
        from src.cache.ttl_cache import TTLCache, _get_disk_cache_path

        monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
        cache = TTLCache(default_ttl=60)
        cache.set("raw_api_payload", ("test_orgs", "test_devices", "test_activities"))

        # Verify disk cache file exists
        p = _get_disk_cache_path("raw_api_payload")
        assert p is not None
        assert p.exists()

        # New cache instance reading from disk
        new_cache = TTLCache(default_ttl=60)
        loaded = new_cache.get("raw_api_payload")
        assert loaded == ("test_orgs", "test_devices", "test_activities")

        # Stale retrieval works
        stale = new_cache.get_stale("raw_api_payload")
        assert stale == ("test_orgs", "test_devices", "test_activities")

        # Clear cleans up disk
        new_cache.clear()
        assert not p.exists()

    def test_selected_patch_titles_direct_override_and_zero_threshold_compliance(self):
        from src.metrics.patch_compliance import compute_patch_metrics

        # Server 1 has uninstalled custom software patch that would normally be excluded (Office patch)
        s1 = Device(
            id=301,
            organizationId=1,
            nodeClass="WINDOWS_SERVER",
            displayName="SRV-OFFICE-01",
            approved_patch_count=1,
            os_security_patch_count=0,
            os_security_patch_names=["Security Update for Microsoft Office 2016 (KB5002457)"],
        )
        # Server 2 has no pending patches
        s2 = Device(
            id=302,
            organizationId=1,
            nodeClass="WINDOWS_SERVER",
            displayName="SRV-CLEAN-02",
            approved_patch_count=0,
            os_security_patch_count=0,
            os_security_patch_names=[],
        )

        # Without selecting the title, Office patch is excluded -> both servers are Compliant
        res_default = compute_patch_metrics([s1, s2], org_name_map={1: "Acme Corp"}, patch_type="os")
        assert res_default["compliant_count"] == 2
        assert res_default["non_compliant_count"] == 0

        # With title selected in selected_patch_titles, s1 is directly flagged as Non-Compliant
        res_override = compute_patch_metrics(
            [s1, s2],
            org_name_map={1: "Acme Corp"},
            patch_type="os",
            selected_patch_titles=["Security Update for Microsoft Office 2016 (KB5002457)"],
        )
        assert res_override["compliant_count"] == 1
        assert res_override["non_compliant_count"] == 1
        s1_row = next(r for r in res_override["server_compliance_table"] if r["device_id"] == 301)
        assert s1_row["is_compliant"] is False
        assert s1_row["status"] == "Non-Compliant"

    def test_dynamic_recalculation_with_all_uninstalled_patch_names(self):
        from src.metrics.patch_compliance import compute_patch_metrics

        # Server with generic uninstalled patches in all_uninstalled_patch_names
        dev = Device(
            id=401,
            organizationId=1,
            nodeClass="WINDOWS_SERVER",
            displayName="SRV-DYNAMIC-01",
            all_uninstalled_patch_names=[
                "Special Feature Pack 2024",
                "2024-10 Cumulative Update for Windows Server 2022",
            ],
        )

        # Default keywords: includes "Cumulative Update", so 1 match -> Non-compliant
        res1 = compute_patch_metrics([dev], patch_type="os")
        assert res1["non_compliant_count"] == 1
        assert res1["compliant_count"] == 0

        # Change keywords to only look for "Special Feature": now matched as well
        res2 = compute_patch_metrics([dev], patch_type="os", included_keywords=["Special Feature"])
        assert res2["non_compliant_count"] == 1

        # Change keywords to look for non-existent keyword "NonExistentPatch": now compliant!
        res3 = compute_patch_metrics([dev], patch_type="os", included_keywords=["NonExistentPatch"])
        assert res3["compliant_count"] == 1
        assert res3["non_compliant_count"] == 0

    def test_compute_dashboard_slice_region_fuzzy_matching(self):
        from src.metrics.aggregator import compute_dashboard_slice
        from src.api.models import Organization

        orgs = [Organization(id=1, name="EMEA Corp")]
        devs = [
            Device(id=501, organizationId=1, nodeClass="WINDOWS_SERVER", region="EMEA / Europe", location_name="Frankfurt DC", ipAddress="10.1.1.1"),
            Device(id=502, organizationId=1, nodeClass="WINDOWS_SERVER", region="USA / North America", location_name="New York Office", ipAddress="10.2.2.2"),
        ]

        # Slicing by "Europe" should match "EMEA / Europe"
        slice_res = compute_dashboard_slice(
            devices=devs,
            organizations=orgs,
            activities=[],
            active_region="Europe",
        )
        assert slice_res.active_region == "Europe"
        assert slice_res.total_servers == 1
        assert slice_res.devices_raw[0].id == 501


