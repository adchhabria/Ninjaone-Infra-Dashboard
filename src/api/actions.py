"""
NinjaOne Device & Patch Operational Action Triggers.

Allows triggering remote patch scans and reboot actions against endpoints.
"""

from __future__ import annotations

from typing import Any

from src.api.client import NinjaOneClient, NinjaAPIError


def trigger_patch_scan(client: NinjaOneClient, device_id: int) -> dict[str, Any]:
    """
    Trigger a remote patch scan on a specific NinjaOne device.
    POST /v2/device/{id}/action/patch-scan
    """
    try:
        resp = client.post(f"/v2/device/{device_id}/action/patch-scan", json={})
        return {"success": True, "device_id": device_id, "message": "Patch scan initiated successfully."}
    except NinjaAPIError as err:
        return {"success": False, "device_id": device_id, "error": str(err)}


def trigger_device_reboot(client: NinjaOneClient, device_id: int) -> dict[str, Any]:
    """
    Trigger a remote restart on a specific NinjaOne device.
    POST /v2/device/{id}/action/reboot
    """
    try:
        resp = client.post(f"/v2/device/{device_id}/action/reboot", json={"mode": "FORCED"})
        return {"success": True, "device_id": device_id, "message": "Device reboot scheduled."}
    except NinjaAPIError as err:
        return {"success": False, "device_id": device_id, "error": str(err)}
