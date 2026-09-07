"""
Patch Compliance Metrics Engine.

Revised Compliance Rule:
- Device is COMPLIANT if its Approved Patch Count == 0
- Device is NON-COMPLIANT if its Approved Patch Count >= 1
- Overall Coverage % = (Compliant Devices / Total Devices) * 100
"""

from __future__ import annotations

from typing import Any
from src.api.models import Device, Activity


def get_device_approved_patch_count(device: Device) -> int:
    """
    Extracts the Approved Patch Count for a device:
    - 0 means compliant
    - >= 1 means non-compliant
    """
    # 1. Direct attribute on Device if present
    if hasattr(device, "approved_patch_count") and getattr(device, "approved_patch_count") is not None:
        try:
            return int(getattr(device, "approved_patch_count"))
        except (ValueError, TypeError):
            pass

    cf = device.custom_fields or {}
    refs = device.references or {}

    # 2. Check well-known custom fields
    for key in [
        "approvedPatchCount",
        "approved_patch_count",
        "Approved Patch Count",
        "ApprovedPatches",
        "approved_patches",
        "approvedPatchesPending",
        "approved_patches_pending",
        "totalPatchesPending",
        "total_patches_pending",
        "criticalPatchesPending",
        "pendingPatches",
    ]:
        if key in cf and cf[key] is not None:
            try:
                return int(cf[key])
            except (ValueError, TypeError):
                pass
        if key in refs and refs[key] is not None:
            try:
                return int(refs[key])
            except (ValueError, TypeError):
                pass

    return 0


def compute_patch_metrics(
    devices: list[Device],
    activities: list[Activity] | None = None,
    days: int = 30,
) -> dict[str, Any]:
    """
    Computes fleet patch compliance based strictly on Approved Patch Count:
    - Approved Patch Count == 0: Compliant
    - Approved Patch Count >= 1: Non-Compliant
    """
    total_devices = len(devices)
    if total_devices == 0:
        return {
            "patch_coverage_pct": 100.0,
            "compliant_count": 0,
            "non_compliant_count": 0,
            "total_devices": 0,
            "org_patch_table": [],
        }

    compliant_count = 0
    non_compliant_count = 0
    org_patch_map: dict[int, dict[str, Any]] = {}

    for d in devices:
        cnt = get_device_approved_patch_count(d)
        is_compliant = (cnt == 0)

        if is_compliant:
            compliant_count += 1
        else:
            non_compliant_count += 1

        org_id = d.organization_id
        if org_id not in org_patch_map:
            org_patch_map[org_id] = {
                "org_id": org_id,
                "total": 0,
                "compliant": 0,
                "non_compliant": 0,
            }
        org_patch_map[org_id]["total"] += 1
        if is_compliant:
            org_patch_map[org_id]["compliant"] += 1
        else:
            org_patch_map[org_id]["non_compliant"] += 1

    patch_coverage_pct = round((compliant_count / total_devices * 100), 1)

    org_patch_table = []
    for org_id, v in org_patch_map.items():
        pct = round((v["compliant"] / v["total"] * 100), 1) if v["total"] > 0 else 100.0
        org_patch_table.append({
            "org_id": org_id,
            "patch_pct": pct,
            "compliant": v["compliant"],
            "non_compliant": v["non_compliant"],
            "total": v["total"],
        })

    return {
        "patch_coverage_pct": patch_coverage_pct,
        "compliant_count": compliant_count,
        "non_compliant_count": non_compliant_count,
        "total_devices": total_devices,
        "org_patch_table": org_patch_table,
    }
