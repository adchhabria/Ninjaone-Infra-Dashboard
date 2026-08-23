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
