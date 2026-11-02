"""Tests for Patch SLA aging, classification and operations."""

import pytest
from src.api.models import Device, OSInfo, Activity
from src.metrics.patch_sla import compute_patch_sla_metrics, SLA_BUCKETS


def make_device(
    device_id: int = 1,
    org_id: int = 1,
    crit_patches: int = 2,
    total_patches: int = 4,
    node_class: str = "WINDOWS_WORKSTATION",
) -> Device:
    return Device(
        id=device_id,
        organizationId=org_id,
        nodeClass=node_class,
        displayName=f"PC-{device_id}",
        os=OSInfo(name="Windows 11 23H2"),
        custom_fields={
            "criticalPatchesPending": crit_patches,
            "totalPatchesPending": total_patches,
        },
    )


class TestPatchSLA:
    def test_compute_empty_devices(self):
        result = compute_patch_sla_metrics([], [])
        assert result["total_pending_patches"] == 0
        assert len(result["reboot_devices"]) == 0
        assert len(result["failed_patches"]) == 0

    def test_compute_sla_buckets(self):
        devices = [
            make_device(1, crit_patches=3, total_patches=6),
            make_device(2, crit_patches=0, total_patches=2),
        ]
        result = compute_patch_sla_metrics(devices, [])
        assert result["total_pending_patches"] == 8
        assert "OS Security Updates" in result["type_counts"]
        assert "< 7 Days (Within SLA)" in result["sla_counts"]

    def test_reboot_and_failure_detection(self):
        devices = [make_device(i, crit_patches=1, total_patches=2) for i in range(1, 15)]
        result = compute_patch_sla_metrics(devices, [])
        assert result["reboot_required_count"] > 0
        assert result["failed_patches_count"] > 0

    def test_top_servers_and_top_patches_tables(self):
        d1 = make_device(1, crit_patches=5, total_patches=10)
        d1.device_role = "Domain Controller"
        d1.approved_patch_count = 10
        d1.location_name = "HQ"

        d2 = make_device(2, crit_patches=1, total_patches=3)
        d2.device_role = "Database Server"
        d2.approved_patch_count = 3
        d2.location_name = "Branch"

        raw_os = [
            {"deviceId": 1, "name": "KB5044281 - Security Update", "severity": "CRITICAL", "type": "OS", "timestamp": 1729000000},
            {"deviceId": 2, "name": "KB5044281 - Security Update", "severity": "CRITICAL", "type": "OS", "timestamp": 1729000000},
            {"deviceId": 1, "name": "KB5034441 - Cumulative Update", "severity": "IMPORTANT", "type": "OS", "timestamp": 1728000000},
        ]
        raw_sw = [
            {"deviceId": 1, "productName": "Google Chrome", "severity": "CRITICAL", "type": "Software", "timestamp": 1729500000},
        ]

        result = compute_patch_sla_metrics(
            [d1, d2],
            [],
            org_name_map={1: "Acme Corp"},
            raw_os_patches=raw_os,
            raw_sw_patches=raw_sw,
        )

        top_servers = result["top_servers_pending_patches"]
        assert len(top_servers) == 2
        assert top_servers[0]["name"] == "PC-1"
        assert top_servers[0]["approved_patch_count"] == 10
        assert top_servers[0]["org_name"] == "Acme Corp"
        assert top_servers[0]["location"] == "HQ"

        top_patches = result["top_patches_pending_servers"]
        assert len(top_patches) >= 2
        # KB5044281 has 2 pending devices, should be ranked first
        assert top_patches[0]["patch_name"] == "KB5044281 - Security Update"
        assert top_patches[0]["pending_device_count"] == 2
        assert top_patches[0]["severity"] == "CRITICAL"
        assert "OS" in top_patches[0]["patch_category"]

