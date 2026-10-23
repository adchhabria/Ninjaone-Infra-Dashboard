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
    Extracts the total Approved Patch Count for a device.
    """
    # 1. Direct attribute on Device if explicitly set
    attr_val = getattr(device, "approved_patch_count", None)
    if attr_val is not None:
        return max(0, int(attr_val))

    cf = device.custom_fields or {}
    refs = device.references or {}

    # 2. Check well-known custom fields for approved or pending patches
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
        "patchesPending",
    ]:
        if key in cf and cf[key] is not None:
            try:
                cnt = int(cf[key])
                if cnt > 0:
                    return cnt
            except (ValueError, TypeError):
                pass
        if key in refs and refs[key] is not None:
            try:
                cnt = int(refs[key])
                if cnt > 0:
                    return cnt
            except (ValueError, TypeError):
                pass

    # 3. Check patch status indicators
    if cf.get("patchStatus") == "PENDING" or cf.get("criticalPatchesPending", 0) > 0:
        return max(1, int(cf.get("totalPatchesPending") or cf.get("criticalPatchesPending") or 1))

    # Explicit 0 from attribute or custom field
    if attr_val == 0:
        return 0

    return 0


def get_device_os_security_patch_info(
    device: Device,
    included_keywords: list[str] | None = None,
    excluded_products: list[str] | None = None,
    selected_patch_titles: list[str] | None = None,
) -> tuple[int, list[str]]:
    """
    Extracts the uninstalled approved OS Cumulative/Security update count and patch titles for a device.
    - 0 means compliant (no OS Cumulative or Security updates awaiting installation)
    - >= 1 means non-compliant
    """
    from src.api.patches import is_os_security_or_cumulative_patch

    # 1. Evaluate uninstalled patch list if names are available
    raw_uninstalled = getattr(device, "all_uninstalled_patch_names", None) or getattr(device, "os_security_patch_names", None)
    if raw_uninstalled:
        matching_names = [
            n for n in raw_uninstalled
            if is_os_security_or_cumulative_patch(
                n,
                included_keywords=included_keywords,
                excluded_products=excluded_products,
                selected_patch_titles=selected_patch_titles,
            )
        ]
        return len(matching_names), matching_names

    # 2. Check explicit os_security_patch_count attribute
    cnt_attr = getattr(device, "os_security_patch_count", None)
    if cnt_attr is not None:
        return max(0, int(cnt_attr)), []

    # 3. Fallback to custom fields
    cf = device.custom_fields or {}
    for key in ["osSecurityPatchCount", "os_security_patch_count", "criticalPatchesPending"]:
        if key in cf and cf[key] is not None:
            try:
                cnt = int(cf[key])
                if cnt >= 0:
                    return cnt, []
            except (ValueError, TypeError):
                pass

    # 4. Fallback to approved_patch_count if present
    legacy_cnt = get_device_approved_patch_count(device)
    return legacy_cnt, []


def get_device_approved_software_count(device: Device) -> int:
    """
    Extracts or infers the Approved 3rd-party Software update count for a device.
    """
    attr_val = getattr(device, "approved_software_count", None)
    if attr_val is not None and attr_val >= 0:
        return int(attr_val)

    cf = device.custom_fields or {}
    refs = device.references or {}

    for key in [
        "approvedSoftwareCount",
        "approved_software_count",
        "Approved Software Count",
        "approvedSoftware",
        "approved_software",
        "softwarePatchesPending",
        "totalSoftwarePending",
        "softwarePending",
        "software_pending",
        "pendingSoftware",
        "softwareUpdates",
    ]:
        if key in cf and cf[key] is not None:
            try:
                cnt = int(cf[key])
                if cnt >= 0:
                    return cnt
            except (ValueError, TypeError):
                pass
        if key in refs and refs[key] is not None:
            try:
                cnt = int(refs[key])
                if cnt >= 0:
                    return cnt
            except (ValueError, TypeError):
                pass

    return 0


def compute_patch_metrics(
    devices: list[Device],
    activities: list[Activity] | None = None,
    org_name_map: dict[int, str] | None = None,
    max_approved_patches: int = 0,
    patch_type: str = "both",
    included_keywords: list[str] | None = None,
    excluded_products: list[str] | None = None,
    selected_patch_titles: list[str] | None = None,
) -> dict[str, Any]:
    """
    Computes fleet patch compliance based strictly on uninstalled approved OS Cumulative & Security Updates:
    - patch_type="both": Evaluates OS Cumulative/Security updates plus 3rd-party Software patches
    - patch_type="os": Evaluates only OS Cumulative/Security updates (excluding .NET, Office, SQL)
    - patch_type="software": Evaluates only 3rd-party Software update patches
    - Zero Qualifying Uninstalled Patches (cnt == 0): Compliant
    - Any Qualifying Uninstalled Patches (cnt > 0): Non-Compliant
    - Also generates the Server Patch & Software Compliance ledger with exact offending KBs.
    """
    p_type = (patch_type or "both").lower()
    org_map = org_name_map or {}
    total_devices = len(devices)
    if total_devices == 0:
        return {
            "patch_coverage_pct": 100.0,
            "compliant_count": 0,
            "non_compliant_count": 0,
            "total_devices": 0,
            "org_patch_table": [],
            "max_approved_patches": 0,
            "patch_type": p_type,
            "server_compliance_table": [],
            "server_compliant_count": 0,
            "server_non_compliant_count": 0,
            "server_total_count": 0,
            "server_compliance_pct": 100.0,
        }

    compliant_count = 0
    non_compliant_count = 0
    org_patch_map: dict[int, dict[str, Any]] = {}

    for d in devices:
        os_sec_cnt, _ = get_device_os_security_patch_info(
            d,
            included_keywords=included_keywords,
            excluded_products=excluded_products,
            selected_patch_titles=selected_patch_titles,
        )
        sw_cnt = get_device_approved_software_count(d)

        if p_type == "os":
            cnt = os_sec_cnt
        elif p_type == "software":
            cnt = sw_cnt
        else:
            cnt = os_sec_cnt + sw_cnt

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

    # Build Dedicated Server Patch & Software Compliance Table
    server_devices = [d for d in devices if d.is_server]
    if not server_devices:
        server_devices = devices

    server_compliance_table = []
    server_compliant_count = 0
    server_non_compliant_count = 0

    for s in server_devices:
        s_sec_cnt, s_sec_names = get_device_os_security_patch_info(
            s,
            included_keywords=included_keywords,
            excluded_products=excluded_products,
            selected_patch_titles=selected_patch_titles,
        )
        p_cnt = get_device_approved_patch_count(s)
        sw_cnt = get_device_approved_software_count(s)

        if p_type == "os":
            eval_cnt = s_sec_cnt
        elif p_type == "software":
            eval_cnt = sw_cnt
        else:
            eval_cnt = s_sec_cnt + sw_cnt

        s_compliant = (eval_cnt == 0)

        if s_compliant:
            server_compliant_count += 1
        else:
            server_non_compliant_count += 1

        s_org = org_map.get(s.organization_id, f"Org {s.organization_id}")
        s_loc = s.location_name or "HQ"

        server_compliance_table.append({
            "device_id": s.id,
            "name": s.display_name or s.system_name or f"Server-{s.id}",
            "org_name": s_org,
            "location": s_loc,
            "os": s.os_display,
            "os_security_patch_count": s_sec_cnt,
            "os_security_patch_names": s_sec_names,
            "pending_security_patches_str": ", ".join(s_sec_names) if s_sec_names else "None (Clean)",
            "approved_patch_count": p_cnt,
            "approved_software_count": sw_cnt,
            "effective_patch_count": eval_cnt,
            "status": "Compliant" if s_compliant else "Non-Compliant",
            "is_compliant": s_compliant,
        })

    # Sort server table: Non-Compliant first, then descending by effective patch count
    server_compliance_table.sort(key=lambda r: (r["is_compliant"], -r["effective_patch_count"]))
    server_total = len(server_devices)
    server_compliance_pct = round(server_compliant_count / server_total * 100, 1) if server_total > 0 else 100.0

    return {
        "patch_coverage_pct": patch_coverage_pct,
        "compliant_count": compliant_count,
        "non_compliant_count": non_compliant_count,
        "total_devices": total_devices,
        "org_patch_table": org_patch_table,
        "max_approved_patches": max_approved_patches,
        "patch_type": p_type,
        "server_compliance_table": server_compliance_table,
        "server_compliant_count": server_compliant_count,
        "server_non_compliant_count": server_non_compliant_count,
        "server_total_count": server_total,
        "server_compliance_pct": server_compliance_pct,
    }
