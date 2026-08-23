"""API wrappers for /v2/alerts."""

from __future__ import annotations

from src.api.client import NinjaOneClient
from src.api.models import Alert


def get_active_alerts(client: NinjaOneClient) -> list[Alert]:
    """Fetch all currently active/triggered alerts."""
    raw = client.get("/v2/alerts")
    if not raw:
        return []
    if isinstance(raw, list):
        return [Alert.model_validate(a) for a in raw if isinstance(a, dict)]
    # Some API versions wrap in a results key
    items = raw.get("results", [])
    return [Alert.model_validate(a) for a in items if isinstance(a, dict)]


def get_device_alerts(client: NinjaOneClient, device_id: int) -> list[Alert]:
    """Fetch alerts for a specific device."""
    raw = client.get(f"/v2/device/{device_id}/alerts")
    if not raw:
        return []
    return [Alert.model_validate(a) for a in raw if isinstance(a, dict)]
