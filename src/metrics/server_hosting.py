"""
Server & Device Hosting Infrastructure Classification & Intelligence.

Classifies all devices into:
- Azure Server: Device make contains 'Microsoft Corporation'
- AWS Server: Device make contains 'Amazon EC2' or 'Xen'
- VM Server: Device make contains 'VMware, Inc.' or 'VMware'
- Physical Server: Any other make (HPE, Lenovo, Dell, Supermicro, etc.)

Groups:
- On-Premise (Physical & VMs)
- Cloud (Azure & AWS)
"""

from __future__ import annotations

from typing import Any, Optional
from src.api.models import Device


def get_device_make(device: Device) -> str:
    """Extracts hardware manufacturer/make from system, OS, or custom fields."""
    candidates = [
        device.system_info.manufacturer if device.system_info else "",
        device.system_info.model if device.system_info else "",
        device.os.manufacturer if device.os else "",
        str(device.custom_fields.get("manufacturer", "")) if device.custom_fields else "",
        str(device.custom_fields.get("make", "")) if device.custom_fields else "",
        str(device.custom_fields.get("model", "")) if device.custom_fields else "",
    ]
    for c in candidates:
        if c and str(c).strip() and str(c).strip().lower() not in ["none", "unknown"]:
            return str(c).strip()
    return "Generic Hardware"


def _is_server(device: Device) -> bool:
    """Returns True if device is classified as a server."""
    return bool(device.is_server)


def detect_hosting(device: Device) -> str:
    """
    Classifies device hosting according to hardware make / vendor:
    - Microsoft Corporation -> Azure Server
    - Amazon EC2 / Xen -> AWS Server
    - VMware, Inc. -> VM Server
    - Any other -> Physical Server
    """
    # 1. Explicit override in custom fields or hosting_type if specified
    if device.hosting_type:
        ht = device.hosting_type
        if ht in ["Azure Server", "AWS Server", "VM Server", "Physical Server"]:
            return ht
        ht_lower = ht.lower()
        if "azure" in ht_lower:
            return "Azure Server"
        if "aws" in ht_lower or "amazon" in ht_lower:
            return "AWS Server"
        if "vm" in ht_lower or "virtual" in ht_lower:
            return "VM Server"
        if "gcp" in ht_lower or "google" in ht_lower:
            return "GCP"
        return "Physical Server"

    make = get_device_make(device).lower()

    # Azure Server
    if "microsoft corporation" in make or "microsoft" in make:
        return "Azure Server"

    # AWS Server
    if any(k in make for k in ["amazon ec2", "amazon", "xen", "aws"]):
        return "AWS Server"

    # VM Server (VMware)
    if "vmware" in make:
        return "VM Server"

    # Check tags as secondary indicator
    if device.tags:
        for t in device.tags:
            tl = t.lower()
            if "azure" in tl:
                return "Azure Server"
            if "aws" in tl or "ec2" in tl:
                return "AWS Server"
            if "vmware" in tl or "virtual" in tl:
                return "VM Server"

    # Default to Physical Server (Dell, HPE, Lenovo, Supermicro, Cisco, etc.)
    return "Physical Server"


def get_hosting_group(hosting_type: str) -> str:
    """Returns whether hosting type is Cloud or On-Premise."""
    if hosting_type in ["Azure Server", "AWS Server"]:
        return "Cloud"
    return "On-Premise"


def compute_server_metrics(devices: list[Device], org_name_map: Optional[dict[int, str]] = None) -> dict[str, Any]:
    """
    Computes hosting infrastructure distribution across all devices and organization breakdown.
    """
    org_map = org_name_map or {}
    total = len(devices)

    hosting_counts = {
        "Azure Server": 0,
        "AWS Server": 0,
        "VM Server": 0,
        "Physical Server": 0,
    }

    # Org-wise hosting breakdown: org_id -> dict
    org_breakdown: dict[int, dict[str, Any]] = {}

    server_count = 0
    online_servers = 0
    role_counts: dict[str, int] = {}

    for d in devices:
        h_type = detect_hosting(d)
        d.hosting_type = h_type
        hosting_counts[h_type] = hosting_counts.get(h_type, 0) + 1

        # Track servers
        if d.is_server:
            server_count += 1
            if d.is_online:
                online_servers += 1
            # Simple role detection
            name = (d.display_name or d.system_name or "").lower()
            if any(k in name for k in ["dc", "domain", "ad0", "adds"]):
                r = "Domain Controller"
            elif any(k in name for k in ["fs", "file", "share", "nas"]):
                r = "File Server"
            elif any(k in name for k in ["sql", "db", "postgres", "mysql"]):
                r = "Database Server"
            elif any(k in name for k in ["web", "iis", "nginx", "apache"]):
                r = "Web Server"
            else:
                r = "Application Server"
            role_counts[r] = role_counts.get(r, 0) + 1

        # Track org distribution
        org_id = d.organization_id
        if org_id not in org_breakdown:
            org_breakdown[org_id] = {
                "org_id": org_id,
                "org_name": org_map.get(org_id, f"Org {org_id}"),
                "azure": 0,
                "aws": 0,
                "vm": 0,
                "physical": 0,
                "total": 0,
            }

        org_breakdown[org_id]["total"] += 1
        if h_type == "Azure Server":
            org_breakdown[org_id]["azure"] += 1
        elif h_type == "AWS Server":
            org_breakdown[org_id]["aws"] += 1
        elif h_type == "VM Server":
            org_breakdown[org_id]["vm"] += 1
        else:
            org_breakdown[org_id]["physical"] += 1

    cloud_total = hosting_counts["Azure Server"] + hosting_counts["AWS Server"] + hosting_counts.get("GCP", 0)
    onprem_total = hosting_counts["VM Server"] + hosting_counts["Physical Server"]

    server_online_pct = round((online_servers / server_count * 100), 1) if server_count > 0 else 100.0

    # Aliases for backwards compatibility with tests and legacy consumers
    hosting_counts["AWS"] = hosting_counts["AWS Server"]
    hosting_counts["Azure"] = hosting_counts["Azure Server"]
    hosting_counts["GCP"] = hosting_counts.get("GCP", 0)
    hosting_counts["Virtual Machines (VMs)"] = hosting_counts["VM Server"]
    hosting_counts["Physical Hardware"] = hosting_counts["Physical Server"]
    # Sorted list of org distributions
    org_dist_list = sorted(list(org_breakdown.values()), key=lambda x: x["total"], reverse=True)

    return {
        "hosting_counts": hosting_counts,
        "cloud_total": cloud_total,
        "onprem_total": onprem_total,
        "total_devices": total,
        "org_distribution": org_dist_list,
        "server_count": server_count,
        "online_servers": online_servers,
        "server_online_pct": server_online_pct,
        "role_counts": role_counts,
    }
