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
    Fetch all device roles from NinjaOne GET /v2/roles.
    Returns mapping of {role_id: role_name}, e.g. {1: "Windows Server", 2: "Domain Controller"}.
    """
    try:
        raw = client.get("/v2/roles")
        if isinstance(raw, list):
            return {
                int(r["id"]): str(r["name"]).strip()
                for r in raw
                if isinstance(r, dict) and "id" in r and "name" in r
            }
    except Exception as e:
        print(f"[!] Notice: Could not fetch /v2/roles from NinjaOne: {e}")
    return {}
