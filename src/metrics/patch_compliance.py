"""
Patch Compliance Metrics.

Derives patch health from NinjaOne device data and activity logs.
Computes:
- Overall patch coverage %
- Pending patches by severity
- Time-to-patch trend (30-day rolling)
- Per-organization patch status
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import pandas as pd

from src.api.models import Activity, Device


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SEVERITY_ORDER = ["CRITICAL", "IMPORTANT", "MODERATE", "LOW", "UNKNOWN"]

_PATCH_ACTIVITY_TYPES = {
    "PATCH_MANAGEMENT",
    "PATCH_INSTALL",
    "SOFTWARE_PATCH",
    "WINDOWS_UPDATE",
}


def _extract_patch_activities(activities: list[Activity]) -> pd.DataFrame:
    """Filter and flatten patch-related activities into a DataFrame."""
    rows = []
    for a in activities:
        atype = (a.type or "").upper()
        if any(pt in atype for pt in _PATCH_ACTIVITY_TYPES):
            rows.append(
                {
                    "device_id": a.device_id,
                    "device_name": a.device_name,
                    "org_id": a.organization_id,
                    "activity_time": a.activity_time,
                    "status": (a.status or "").upper(),
                    "status_code": (a.status_code or "").upper(),
                    "subject": a.subject or "",
                }
            )
    return pd.DataFrame(rows)


def _device_patch_compliance(device: Device) -> dict[str, Any]:
    """
    Derive patch compliance from device custom fields or references.
    NinjaOne exposes patch data in custom fields; we check common field names.
    """
    cf = device.custom_fields or {}
    refs = device.references or {}

    # Attempt to read patch status from well-known custom fields
    patch_status = (
        cf.get("patchStatus")
        or cf.get("patch_status")
        or cf.get("windowsUpdateStatus")
        or refs.get("patchStatus")
        or "UNKNOWN"
    )
    critical_pending = int(
        cf.get("criticalPatchesPending") or cf.get("critical_patches_pending") or 0
    )
    total_pending = int(
        cf.get("totalPatchesPending") or cf.get("total_patches_pending") or 0
    )

    return {
        "id": device.id,
        "name": device.display_name or device.system_name or f"Device-{device.id}",
        "org_id": device.organization_id,
        "patch_status": str(patch_status).upper(),
        "critical_pending": critical_pending,
        "total_pending": total_pending,
        "is_compliant": critical_pending == 0 and str(patch_status).upper() != "FAILED",
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_patch_metrics(
    devices: list[Device],
    activities: list[Activity],
    days: int = 30,
) -> dict[str, Any]:
    """
    Compute patch compliance metrics from devices and activity log.

    Returns:
        patch_coverage_pct:     float — % of devices with no critical patches pending
        pending_by_severity:    {severity: count}
        trend_data:             list[{date, success, failed}] — 30-day daily counts
        org_patch_table:        list[dict] — per-org patch compliance rows
        devices_needing_patches: list[dict] — non-compliant device list
    """
    # Per-device compliance from custom fields
    device_rows = [_device_patch_compliance(d) for d in devices]
    device_df = pd.DataFrame(device_rows)

    # Activity trend
    patch_df = _extract_patch_activities(activities)

    if device_df.empty:
        return {
            "patch_coverage_pct": 0.0,
            "pending_by_severity": {},
            "trend_data": [],
            "org_patch_table": [],
            "devices_needing_patches": [],
        }

    total = len(device_df)
    compliant_count = device_df["is_compliant"].sum()
    patch_coverage_pct = round((compliant_count / total) * 100, 1) if total > 0 else 0.0

    # Severity aggregation from pending counts
    critical_total = int(device_df["critical_pending"].sum())
    pending_by_severity = {"CRITICAL": critical_total} if critical_total > 0 else {}

    # Per-org compliance table
    org_table: list[dict] = []
    for org_id, grp in device_df.groupby("org_id"):
        total_grp = len(grp)
        compliant_grp = grp["is_compliant"].sum()
        pct = round((compliant_grp / total_grp) * 100, 1) if total_grp > 0 else 0.0
        critical_sum = int(grp["critical_pending"].sum())
        org_table.append(
            {
                "org_id": int(org_id),
                "device_count": total_grp,
                "compliant_count": int(compliant_grp),
                "patch_pct": pct,
                "critical_pending": critical_sum,
            }
        )

    # Trend data from activity log
    trend_data: list[dict] = []
    if not patch_df.empty:
        patch_df["date"] = pd.to_datetime(patch_df["activity_time"]).dt.date
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).date()
        recent = patch_df[patch_df["date"] >= cutoff]
        if not recent.empty:
            daily = (
                recent.groupby(["date", "status"])
                .size()
                .unstack(fill_value=0)
                .reset_index()
            )
            for _, row in daily.iterrows():
                trend_data.append(
                    {
                        "date": str(row["date"]),
                        "success": int(row.get("SUCCESS", 0)),
                        "failed": int(row.get("FAILED", 0)),
                    }
                )

    non_compliant = device_df[~device_df["is_compliant"]][
        ["id", "name", "org_id", "critical_pending", "total_pending"]
    ].to_dict("records")

    return {
        "patch_coverage_pct": patch_coverage_pct,
        "pending_by_severity": pending_by_severity,
        "trend_data": trend_data,
        "org_patch_table": org_table,
        "devices_needing_patches": non_compliant,
    }
