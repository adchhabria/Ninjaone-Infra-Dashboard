"""
API wrappers for NinjaOne Patch Management endpoints.

Fetches fleet-wide OS and Software patch status:
- /v2/queries/os-patches (fallback: /v2/reports/os-patches/pending-failed-rejected)
- /v2/queries/software-patches (fallback: /v2/reports/software-patches/pending-failed-rejected)

Aggregates approved and pending patch counts per device.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple
from rich.console import Console

from src.api.client import NinjaOneClient

console = Console()


def get_all_os_patches(client: NinjaOneClient) -> list[dict[str, Any]]:
    """
    Fetches OS patch records from NinjaOne fleet query or report endpoints.
    Returns list of patch dicts (containing deviceId, status, name, severity, etc.).
    """
    # 1. Primary fleet query endpoint
    try:
        raw = client.get_paginated("/v2/queries/os-patches", page_size=1000)
        if raw:
            console.log(f"[green]Successfully retrieved {len(raw)} OS patch records from /v2/queries/os-patches[/green]")
            return [p for p in raw if isinstance(p, dict)]
    except Exception as e:
        console.log(f"[yellow]Notice: /v2/queries/os-patches query notice: {e}. Trying fallback...[/yellow]")

    # 2. Fallback report endpoint
    try:
        raw = client.get_paginated("/v2/reports/os-patches/pending-failed-rejected", page_size=1000)
        if raw:
            console.log(f"[green]Successfully retrieved {len(raw)} OS patch records from /v2/reports/os-patches[/green]")
            return [p for p in raw if isinstance(p, dict)]
    except Exception as e:
        console.log(f"[dim]Fallback OS patch report notice: {e}[/dim]")

    return []


def get_all_software_patches(client: NinjaOneClient) -> list[dict[str, Any]]:
    """
    Fetches 3rd-party Software patch records from NinjaOne fleet query or report endpoints.
    Returns list of patch dicts (containing deviceId, status, name, etc.).
    """
    # 1. Primary fleet query endpoint
    try:
        raw = client.get_paginated("/v2/queries/software-patches", page_size=1000)
        if raw:
            console.log(f"[green]Successfully retrieved {len(raw)} software patch records from /v2/queries/software-patches[/green]")
            return [p for p in raw if isinstance(p, dict)]
    except Exception as e:
        console.log(f"[yellow]Notice: /v2/queries/software-patches query notice: {e}. Trying fallback...[/yellow]")

    # 2. Fallback report endpoint
    try:
        raw = client.get_paginated("/v2/reports/software-patches/pending-failed-rejected", page_size=1000)
        if raw:
            console.log(f"[green]Successfully retrieved {len(raw)} software patch records from /v2/reports/software-patches[/green]")
            return [p for p in raw if isinstance(p, dict)]
    except Exception as e:
        console.log(f"[dim]Fallback software patch report notice: {e}[/dim]")

    return []


def get_fleet_patch_counts(client: NinjaOneClient) -> Tuple[Dict[int, int], Dict[int, int]]:
    """
    Queries NinjaOne live patch reporting endpoints and aggregates:
    1. os_approved_counts: mapping from device_id -> approved OS patch count
    2. sw_approved_counts: mapping from device_id -> approved software patch count

    Status Evaluation Rule:
    - Status or approvalStatus == "APPROVED": explicitly approved patch awaiting install.
    - Status == "PENDING": pending approval/install (counted if no explicit APPROVED patches exist).
    - Status == "REJECTED": ignored.
    """
    approved_os_map: Dict[int, int] = {}
    pending_os_map: Dict[int, int] = {}

    os_patches = get_all_os_patches(client)
    for p in os_patches:
        dev_id = p.get("deviceId") or p.get("device_id")
        if not dev_id:
            continue
        try:
            dev_id = int(dev_id)
        except (ValueError, TypeError):
            continue

        status = str(p.get("status") or "").upper()
        approval = str(p.get("approvalStatus") or p.get("approval_status") or p.get("approval") or "").upper()
        is_approved_flag = p.get("approved") is True or p.get("isApproved") is True

        is_approved = (
            approval == "APPROVED"
            or status == "APPROVED"
            or is_approved_flag
            or "APPROV" in approval
            or status == "PENDING_INSTALL"
        )

        if is_approved:
            approved_os_map[dev_id] = approved_os_map.get(dev_id, 0) + 1
        elif status not in ["REJECTED", "DECLINED", "IGNORED", "EXCLUDED"]:
            pending_os_map[dev_id] = pending_os_map.get(dev_id, 0) + 1

    # If any patches in the fleet are marked APPROVED, use exact APPROVED counts.
    # Otherwise, if all pending patches share a general PENDING status, use pending counts.
    if approved_os_map:
        os_counts = approved_os_map
    elif pending_os_map:
        os_counts = pending_os_map
    else:
        os_counts = {}

    # Software Patches
    approved_sw_map: Dict[int, int] = {}
    pending_sw_map: Dict[int, int] = {}

    sw_patches = get_all_software_patches(client)
    for sp in sw_patches:
        dev_id = sp.get("deviceId") or sp.get("device_id")
        if not dev_id:
            continue
        try:
            dev_id = int(dev_id)
        except (ValueError, TypeError):
            continue

        status = str(sp.get("status") or "").upper()
        approval = str(sp.get("approvalStatus") or sp.get("approval_status") or sp.get("approval") or "").upper()
        is_approved_flag = sp.get("approved") is True or sp.get("isApproved") is True

        is_approved = (
            approval == "APPROVED"
            or status == "APPROVED"
            or is_approved_flag
            or "APPROV" in approval
            or status == "PENDING_INSTALL"
        )

        if is_approved:
            approved_sw_map[dev_id] = approved_sw_map.get(dev_id, 0) + 1
        elif status not in ["REJECTED", "DECLINED", "IGNORED", "EXCLUDED"]:
            pending_sw_map[dev_id] = pending_sw_map.get(dev_id, 0) + 1

    if approved_sw_map:
        sw_counts = approved_sw_map
    elif pending_sw_map:
        sw_counts = pending_sw_map
    else:
        sw_counts = {}

    return os_counts, sw_counts
