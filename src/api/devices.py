"""API wrappers for /v2/devices and /v2/devices-detailed."""

from __future__ import annotations

from typing import Optional

from src.api.client import NinjaOneClient
from src.api.models import Device


def get_all_devices(client: NinjaOneClient) -> list[Device]:
    """Fetch all devices (paginated). Returns lightweight Device objects."""
    raw = client.paginated_get("/v2/devices")
    return [Device.model_validate(d) for d in raw if isinstance(d, dict)]


def get_devices_detailed(client: NinjaOneClient, page_size: int = 1000) -> list[Device]:
    """
    Fetch detailed device info including OS, system info, and custom fields.
    Uses /v2/devices-detailed which is heavier — cached aggressively.
    """
    raw = client.paginated_get("/v2/devices-detailed", page_size=page_size)
    return [Device.model_validate(d) for d in raw if isinstance(d, dict)]


def get_device(client: NinjaOneClient, device_id: int) -> Optional[Device]:
    """Fetch a single device by ID."""
    raw = client.get(f"/v2/device/{device_id}")
    return Device.model_validate(raw) if raw else None


def get_device_roles(client: NinjaOneClient) -> dict[int, str]:
    """
    Fetch all device roles from NinjaOne GET /v2/roles or /v2/device-roles.
    Returns mapping of {role_id: role_name}, e.g. {1: "Windows Server", 2: "Domain Controller"}.
    """
    for endpoint in ("/v2/roles", "/v2/device-roles", "/v2/roles/device"):
        try:
            raw = client.get(endpoint)
            role_items = []
            if isinstance(raw, list):
                role_items = raw
            elif isinstance(raw, dict):
                role_items = raw.get("roles") or raw.get("results") or raw.get("data") or []

            if isinstance(role_items, list) and role_items:
                roles = {
                    int(r["id"]): str(r.get("name") or r.get("description") or f"Role {r['id']}").strip()
                    for r in role_items
                    if isinstance(r, dict) and "id" in r and (r.get("name") or r.get("description"))
                }
                if roles:
                    return roles
        except Exception as e:
            pass
    return {}
