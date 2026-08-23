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
