"""
Server Roles & Multi-Cloud / Virtualization Hosting Metrics.

Classifies servers into:
- Roles: Domain Controller, File, Web, Database, Application, Backup
- Hosting Infrastructure: AWS, Azure, GCP, Physical Hardware, Virtual Machines (VMs)

Uses a multi-tier detection algorithm:
1. Explicit metadata (tags, custom fields, hosting_type)
2. BIOS & System Hardware Info (systemInfo.manufacturer, systemInfo.model, chassisType)
3. Node Classification (VMware, Hyper-V, Cloud monitor)
4. DNS / Hostname / System naming patterns
"""

from __future__ import annotations

from typing import Any
import pandas as pd
from src.api.models import Device


ROLE_KEYWORDS = {
    "Domain Controller": ["dc", "domain", "ad0", "adds", "activedirectory"],
    "File Server": ["fs", "file", "share", "storage", "nas"],
    "Web Server": ["web", "iis", "nginx", "apache", "http", "frontend"],
    "Database Server": ["sql", "db", "postgres", "mysql", "oracle", "mongo"],
    "Application Server": ["app", "api", "backend", "worker", "service"],
    "Backup Server": ["veeam", "backup", "bck", "commvault"],
}


def _is_server(device: Device) -> bool:
    return device.is_server


def _detect_role(device: Device) -> str:
    name = (device.display_name or device.system_name or "").lower()
    for role, kw_list in ROLE_KEYWORDS.items():
        if any(kw in name for kw in kw_list):
            return role
    return "General Server"


def _detect_hosting(device: Device) -> str:
    """
    Multi-tier detection algorithm for Server Hosting infrastructure.
    """
    # 1. Check explicit hosting_type or custom field override
    if device.hosting_type:
        return device.hosting_type
    if device.custom_fields:
        cf_host = device.custom_fields.get("hosting") or device.custom_fields.get("cloud_provider")
        if cf_host:
            cf_val = str(cf_host).lower()
            if "aws" in cf_val or "amazon" in cf_val:
                return "AWS"
            if "azure" in cf_val:
                return "Azure"
            if "gcp" in cf_val or "google" in cf_val:
                return "GCP"
            if "vm" in cf_val or "vmware" in cf_val or "hyper" in cf_val:
                return "Virtual Machines (VMs)"
            if "phys" in cf_val or "bare" in cf_val:
                return "Physical Hardware"

    # 2. Check Tags
    if device.tags:
        for tag in device.tags:
            t = tag.lower()
            if "aws" in t or "ec2" in t:
                return "AWS"
            if "azure" in t:
                return "Azure"
            if "gcp" in t or "google-cloud" in t:
                return "GCP"
            if "vmware" in t or "hyper-v" in t or "virtual" in t:
                return "Virtual Machines (VMs)"
            if "physical" in t or "bare-metal" in t:
                return "Physical Hardware"

    # 3. Check System Info (Hardware Manufacturer & Model reported by Ninja agent)
    sys_info = device.system_info
    if sys_info:
        mfg = (sys_info.manufacturer or "").lower()
        model = (sys_info.model or "").lower()

        # AWS EC2 detection
        if "amazon" in mfg or "amazon" in model or "ec2" in model:
            return "AWS"

        # Azure VM detection
        if "microsoft corporation" in mfg and ("virtual machine" in model or "standard_" in model):
            return "Azure"

        # GCP Compute Engine detection
        if "google" in mfg or "google" in model:
            return "GCP"

        # VMware / Hyper-V / KVM virtualization
        if any(k in mfg for k in ["vmware", "qemu", "innotek", "xen"]) or any(k in model for k in ["vmware", "virtualbox", "kvm"]):
            return "Virtual Machines (VMs)"

        # Physical bare-metal server manufacturers
        if any(k in mfg for k in ["dell", "hp", "hpe", "hewlett", "lenovo", "supermicro", "cisco", "fujitsu"]):
            if not sys_info.virtual_machine:
                return "Physical Hardware"

    # 4. Check Node Class
    nc = (device.node_class or "").lower()
    if any(k in nc for k in ["vmware", "hyper_v", "guest", "virtual"]):
        return "Virtual Machines (VMs)"
    if "cloud" in nc:
        return "AWS"

    # 5. Check Hostname / DNS Patterns
    name = (device.display_name or device.system_name or "").lower()
    dns = (device.dns_name or "").lower()

    if any(k in name for k in ["aws", "ec2", "amazon"]) or "amazonaws.com" in dns:
        return "AWS"
    if any(k in name for k in ["azure", "az-", "-az", "azvm"]) or "azure.com" in dns or "cloudapp.net" in dns:
        return "Azure"
    if any(k in name for k in ["gcp", "google", "gce"]) or "google.internal" in dns:
        return "GCP"
    if any(k in name for k in ["vm-", "-vm", "esxi", "vbox", "hyperv"]):
        return "Virtual Machines (VMs)"

    # 6. Default to Physical Hardware
    return "Physical Hardware"


def compute_server_metrics(devices: list[Device]) -> dict[str, Any]:
    """
    Computes server role breakdown, hosting infrastructure distribution,
    and server online status across the device fleet.
    """
    servers = [d for d in devices if _is_server(d)]
    total_servers = len(servers)

    if total_servers == 0:
        return {
            "server_count": 0,
            "workstation_count": len(devices),
            "role_counts": {},
            "hosting_counts": {
                "AWS": 0, "Azure": 0, "GCP": 0, "Physical Hardware": 0, "Virtual Machines (VMs)": 0
            },
            "server_online_pct": 100.0,
            "online_servers": 0,
        }

    rows = []
    for s in servers:
        role = _detect_role(s)
        hosting = _detect_hosting(s)
        rows.append({
            "id": s.id,
            "name": s.display_name or s.system_name or f"SRV-{s.id}",
            "role": role,
            "hosting": hosting,
            "online": s.is_online,
            "os": s.os_display,
            "region": s.region or "USA / North America",
        })

    df = pd.DataFrame(rows)

    role_counts = df["role"].value_counts().to_dict()
    hosting_counts = df["hosting"].value_counts().to_dict()

    # Ensure all standard hosting categories are present
    for h in ["AWS", "Azure", "GCP", "Physical Hardware", "Virtual Machines (VMs)"]:
        if h not in hosting_counts:
            hosting_counts[h] = 0

    online_servers = int(df["online"].sum())
    server_online_pct = round((online_servers / total_servers) * 100, 1)

    return {
        "server_count": total_servers,
        "workstation_count": len(devices) - total_servers,
        "role_counts": role_counts,
        "hosting_counts": hosting_counts,
        "server_online_pct": server_online_pct,
        "online_servers": online_servers,
    }
