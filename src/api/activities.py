"""API wrappers for /v2/activities (patch activity, audit log)."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from src.api.client import NinjaOneClient
from src.api.models import Activity


def get_recent_activities(
    client: NinjaOneClient,
    days: int = 30,
    activity_type: Optional[str] = None,
    page_size: int = 500,
) -> list[Activity]:
    """
    Fetch recent activities filtered by date.

    Args:
        days:          Look-back window in days.
        activity_type: e.g. 'PATCH_MANAGEMENT', 'CONDITION_TRIGGERED'
        page_size:     Items per page.
    """
    since = datetime.utcnow() - timedelta(days=days)
    params: dict = {"pageSize": page_size, "after": int(since.timestamp())}
    if activity_type:
        params["type"] = activity_type

    raw = client.get("/v2/activities", params=params)
    if not raw:
        return []

    items = raw if isinstance(raw, list) else raw.get("activities", [])
    return [Activity.model_validate(a) for a in items if isinstance(a, dict)]


def get_device_activities(
    client: NinjaOneClient,
    device_id: int,
    days: int = 30,
) -> list[Activity]:
    """Fetch activity log for a specific device."""
    since = datetime.utcnow() - timedelta(days=days)
    params = {"pageSize": 200, "after": int(since.timestamp())}
    raw = client.get(f"/v2/device/{device_id}/activities", params=params)
    if not raw:
        return []
    items = raw if isinstance(raw, list) else raw.get("activities", [])
    return [Activity.model_validate(a) for a in items if isinstance(a, dict)]
