"""
Mock/Sample Data Generator with Geographic, Multi-Cloud Hosting & EOL Intelligence.

Generates realistic NinjaOne-like data so the dashboard can be demoed
without a live API connection, supporting interactive Organization, Location,
and OS Family slicers, World Map visualization, and multi-cloud hosting distributions.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone
from typing import Optional

from src.api.models import Device, Organization, OSInfo, Activity
from src.metrics.aggregator import (
    DashboardData,
    compute_dashboard_slice,
    resolve_geo,
)

SEED = 42
random.seed(SEED)

# ---------------------------------------------------------------------------
# Organizations & Locations with Global Footprint
# ---------------------------------------------------------------------------

ORG_DEFINITIONS = [
    {"id": 1, "name": "Headquarters - New York", "desc": "US Corporate Office", "country": "USA", "region": "USA / North America", "location": "New York HQ"},
    {"id": 2, "name": "London EMEA Hub", "desc": "UK Operations & Finance", "country": "GBR", "region": "EMEA / Europe", "location": "London Office"},
    {"id": 3, "name": "APAC Regional HQ - Singapore", "desc": "Singapore Tech Center", "country": "SGP", "region": "APAC / Asia", "location": "Singapore Tech Park"},
    {"id": 4, "name": "Tokyo Innovation Lab", "desc": "Japan R&D Hub", "country": "JPN", "region": "APAC / Asia", "location": "Tokyo Center"},
    {"id": 5, "name": "Frankfurt Data Center", "desc": "EU Infrastructure & Systems", "country": "DEU", "region": "EMEA / Europe", "location": "Frankfurt DC"},
    {"id": 6, "name": "India Tech Operations - Mumbai", "desc": "Development & QA Center", "country": "IND", "region": "APAC / Asia", "location": "Mumbai Tech Hub"},
    {"id": 7, "name": "Sydney Branch - ANZ", "desc": "Australia Sales & Support", "country": "AUS", "region": "APAC / Asia", "location": "Sydney Hub"},
    {"id": 8, "name": "Sao Paulo LatAm Office", "desc": "Brazil Logistics & Ops", "country": "BRA", "region": "Latin America", "location": "Sao Paulo DC"},
]

WINDOWS_OS_LIST = [
    ("Windows 11 Enterprise 23H2", "23H2", "WINDOWS_WORKSTATION", 0.35),
    ("Windows 11 Pro 22H2", "22H2", "WINDOWS_WORKSTATION", 0.25),
    ("Windows 10 Pro 22H2", "22H2", "WINDOWS_WORKSTATION", 0.15),
    ("Windows 10 Enterprise 21H2", "21H2", "WINDOWS_WORKSTATION", 0.05),  # EOL
    ("Windows Server 2022 Datacenter", "2022", "WINDOWS_SERVER", 0.08),
    ("Windows Server 2019 Standard", "2019", "WINDOWS_SERVER", 0.06),
    ("Windows Server 2012 R2", "2012 R2", "WINDOWS_SERVER", 0.03),        # EOL
    ("Windows 8.1 Pro", None, "WINDOWS_WORKSTATION", 0.02),               # EOL
    ("Windows 7 Professional", None, "WINDOWS_WORKSTATION", 0.01),        # EOL
]

LINUX_OS_LIST = [
    ("Ubuntu 22.04 LTS", "22.04", "LINUX_SERVER", 0.50),
    ("Ubuntu 20.04 LTS", "20.04", "LINUX_SERVER", 0.25),
    ("CentOS 7", None, "LINUX_SERVER", 0.15),                              # EOL
    ("Debian 11", "11", "LINUX_SERVER", 0.10),
]

SERVER_ROLES = [
    "Domain Controller", "File Server", "Web Server",
    "Database Server", "Application Server", "Backup Server",
]

HOSTING_TYPES_LIST = [
    ("Azure", 0.30),
    ("AWS", 0.25),
    ("Virtual Machines (VMs)", 0.20),
    ("GCP", 0.15),
    ("Physical Hardware", 0.10),
]

_CACHED_RAW_MOCK: Optional[tuple[list[Organization], list[Device], list[Activity]]] = None


def _generate_raw_mock() -> tuple[list[Organization], list[Device], list[Activity]]:
    """Generates base mock dataset once and caches in memory."""
    orgs = []
    for od in ORG_DEFINITIONS:
        cc, cname, reg, lat, lon = resolve_geo(od["name"], od["desc"])
        org = Organization(
            id=od["id"],
            name=od["name"],
            description=od["desc"],
            country=od["country"],
            country_code=od["country"],
            region=od["region"],
            latitude=lat,
            longitude=lon,
        )
        orgs.append(org)

    devices = []
    dev_id_counter = 1000

    for od in ORG_DEFINITIONS:
        org_id = od["id"]
        loc_name = od["location"]
        reg = od["region"]
        cc = od["country"]

        # 30 to 65 devices per organization
        num_devs = random.randint(30, 65)
        for i in range(num_devs):
            dev_id_counter += 1
            is_linux = random.random() < 0.22

            if is_linux:
                os_choice = random.choices(
                    LINUX_OS_LIST, weights=[item[3] for item in LINUX_OS_LIST]
                )[0]
                os_name, rid, node_class, _ = os_choice
            else:
                os_choice = random.choices(
                    WINDOWS_OS_LIST, weights=[item[3] for item in WINDOWS_OS_LIST]
                )[0]
                os_name, rid, node_class, _ = os_choice

            is_offline = random.random() < 0.08
            is_srv = "SERVER" in node_class

            hosting_val = None
            if is_srv:
                role = random.choice(SERVER_ROLES)
                role_code = role.replace(" ", "-").upper()
                hosting_val = random.choices(
                    [h[0] for h in HOSTING_TYPES_LIST],
                    weights=[h[1] for h in HOSTING_TYPES_LIST],
                )[0]
                d_name = f"SRV-{cc}-{hosting_val[:3].upper()}-{role_code}-{dev_id_counter % 100:02d}"
            else:
                d_name = f"WS-{cc}-{dev_id_counter % 1000:03d}"

            # Patch simulation
            crit_patches = 0
            if "2012" in os_name or "8.1" in os_name or "7" in os_name or "CentOS 7" in os_name:
                crit_patches = random.randint(1, 4)
            elif random.random() < 0.12:
                crit_patches = random.randint(1, 2)

            total_pending = crit_patches + random.randint(0, 3) if crit_patches > 0 else (random.randint(0, 2) if random.random() < 0.2 else 0)

            device = Device(
                id=dev_id_counter,
                organizationId=org_id,
                nodeClass=node_class,
                displayName=d_name,
                systemName=d_name,
                offline=is_offline,
                region=reg,
                country=cc,
                location_name=loc_name,
                hosting_type=hosting_val,
                approved_patch_count=total_pending,
                lastSeen=datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 72)),
                os=OSInfo(name=os_name, releaseId=rid),
                custom_fields={
                    "approvedPatchCount": total_pending,
                    "criticalPatchesPending": crit_patches,
                    "totalPatchesPending": total_pending,
                    "patchStatus": "PENDING" if crit_patches > 0 else "OK",
                    "hosting": hosting_val,
                },
            )
            devices.append(device)

    # Activities for patch trends
    activities = []
    now = datetime.now(timezone.utc)
    for d in range(30):
        t_date = now - timedelta(days=29 - d)
        num_patches = random.randint(15, 45)
        for _ in range(num_patches):
            is_succ = random.random() > 0.08
            act = Activity(
                id=len(activities) + 1,
                activityTime=t_date,
                organizationId=random.choice(orgs).id,
                type="PATCH_MANAGEMENT",
                status="SUCCESS" if is_succ else "FAILED",
                subject="Windows/Linux Security Update",
            )
            activities.append(act)

    return orgs, devices, activities


def get_mock_dashboard_data(
    active_org_id: Optional[int] = None,
    active_region: Optional[str] = None,
    active_location: Optional[str] = None,
    active_os_family: Optional[str] = None,
    approaching_days: int = 180,
) -> DashboardData:
    """Returns complete DashboardData computed from realistic mock pool."""
    global _CACHED_RAW_MOCK
    if _CACHED_RAW_MOCK is None:
        _CACHED_RAW_MOCK = _generate_raw_mock()

    orgs, devices, activities = _CACHED_RAW_MOCK

    return compute_dashboard_slice(
        devices=devices,
        organizations=orgs,
        activities=activities,
        active_org_id=active_org_id,
        active_region=active_region,
        active_location=active_location,
        active_os_family=active_os_family,
        approaching_days=approaching_days,
    )


if __name__ == "__main__":
    from rich.console import Console
    from rich.table import Table

    console = Console()
    data = get_mock_dashboard_data()

    console.print("\n[bold cyan]NinjaOne Mock Data Summary (Global)[/bold cyan]")
    t = Table(show_header=True, header_style="bold blue")
    t.add_column("Metric")
    t.add_column("Value", justify="right")
    t.add_row("Total Devices", str(data.total_devices))
    t.add_row("Compliance Score", f"{data.overall_compliance_score:.1f}%")
    t.add_row("Servers", str(data.total_servers))
    t.add_row("Server Hosting Breakdown", str(data.servers.get("hosting_counts", {})))
    t.add_row("Locations", str(len(data.location_options)))
    t.add_row("OS Families", str(data.os_family_options))
    console.print(t)
