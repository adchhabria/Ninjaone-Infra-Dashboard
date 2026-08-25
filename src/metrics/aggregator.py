"""
Master Metrics Aggregator & Regional Intelligence Layer.

Single entry point for the dashboard — fetches API data,
assigns geographic intelligence, computes compliance, SLA aging & EOL scoring,
and supports dynamic slicing by Organization, Location, OS Family, and Geographic Region.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

import pandas as pd
from rich.console import Console

from src.api.client import NinjaOneClient
from src.api.devices import get_devices_detailed
from src.api.organizations import get_organizations_detailed
from src.api.activities import get_recent_activities
from src.api.models import Device, Organization, Activity
from src.cache.ttl_cache import get_cache
from src.metrics.os_compliance import compute_os_metrics, _is_eol, _classify_os_family
from src.metrics.server_hosting import compute_server_metrics
from src.metrics.patch_compliance import compute_patch_metrics
from src.metrics.patch_sla import compute_patch_sla_metrics

console = Console()


# ---------------------------------------------------------------------------
# Region & Country Mapping Rules
# ---------------------------------------------------------------------------

REGION_DEFINITIONS = {
    "USA / North America": {
        "label": "USA / North America",
        "iso_codes": ["USA", "CAN", "MEX"],
        "keywords": ["usa", "us", "america", "new york", "headquarters", "chicago", "dallas", "seattle", "canada"],
    },
    "APAC / Asia": {
        "label": "APAC / Asia",
        "iso_codes": ["SGP", "JPN", "IND", "AUS", "HKG", "KOR"],
        "keywords": ["apac", "asia", "singapore", "tokyo", "japan", "india", "mumbai", "hong kong", "australia", "sydney"],
    },
    "EMEA / Europe": {
        "label": "EMEA / Europe",
        "iso_codes": ["GBR", "DEU", "FRA", "NLD", "IRL", "ESP", "ITA"],
        "keywords": ["emea", "europe", "london", "uk", "germany", "frankfurt", "paris", "dublin", "amsterdam"],
    },
    "Latin America": {
        "label": "Latin America",
        "iso_codes": ["BRA", "ARG", "CHL", "COL"],
        "keywords": ["latam", "latin", "brazil", "sao paulo", "mexico", "buenos aires"],
    },
}

COUNTRY_COORDINATES = {
    "USA": {"name": "United States", "lat": 37.0902, "lon": -95.7129, "region": "USA / North America"},
    "GBR": {"name": "United Kingdom", "lat": 55.3781, "lon": -3.4360, "region": "EMEA / Europe"},
    "DEU": {"name": "Germany", "lat": 51.1657, "lon": 10.4515, "region": "EMEA / Europe"},
    "SGP": {"name": "Singapore", "lat": 1.3521, "lon": 103.8198, "region": "APAC / Asia"},
    "JPN": {"name": "Japan", "lat": 36.2048, "lon": 138.2529, "region": "APAC / Asia"},
    "IND": {"name": "India", "lat": 20.5937, "lon": 78.9629, "region": "APAC / Asia"},
    "AUS": {"name": "Australia", "lat": -25.2744, "lon": 133.7751, "region": "APAC / Asia"},
    "BRA": {"name": "Brazil", "lat": -14.2350, "lon": -51.9253, "region": "Latin America"},
}


def resolve_geo(org_name: str, desc: str | None = None) -> tuple[str, str, str, float, float]:
    """
    Infers Country Code, Country Name, Region, Lat, and Lon from Org metadata.
    Returns: (country_code, country_name, region, lat, lon)
    """
    text = f"{org_name} {desc or ''}".lower()

    if any(k in text for k in ["london", "uk", "united kingdom", "emea", "europe", "germany", "frankfurt"]):
        if "germany" in text or "frankfurt" in text:
            return "DEU", "Germany", "EMEA / Europe", 51.1657, 10.4515
        return "GBR", "United Kingdom", "EMEA / Europe", 55.3781, -3.4360

    if any(k in text for k in ["apac", "asia", "singapore", "tokyo", "japan", "india", "mumbai", "australia"]):
        if "tokyo" in text or "japan" in text:
            return "JPN", "Japan", "APAC / Asia", 36.2048, 138.2529
        if "india" in text or "mumbai" in text:
            return "IND", "India", "APAC / Asia", 20.5937, 78.9629
        if "australia" in text or "sydney" in text:
            return "AUS", "Australia", "APAC / Asia", -25.2744, 133.7751
        return "SGP", "Singapore", "APAC / Asia", 1.3521, 103.8198

    if any(k in text for k in ["brazil", "latam", "latin"]):
        return "BRA", "Brazil", "Latin America", -14.2350, -51.9253

    # Default to USA / North America
    return "USA", "United States", "USA / North America", 37.0902, -95.7129


# ---------------------------------------------------------------------------
# Data Container
# ---------------------------------------------------------------------------

@dataclass
class DashboardData:
    """Fully computed metrics package consumed by the UI and Export engines."""

    fetched_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Active Filters
    active_org_id: Optional[int] = None
    active_region: Optional[str] = None
    active_location: Optional[str] = None
    active_os_family: Optional[str] = None
    active_filter_label: str = "Global Overview"

    # KPI Summary
    total_devices: int = 0
    online_devices: int = 0
    online_pct: float = 0.0
    overall_compliance_score: float = 0.0   # 0–100
    compliance_rag: str = "GREEN"           # RED / AMBER / GREEN
    total_servers: int = 0
    eol_risk_count: int = 0

    # OS & EOL Metrics
    os: dict[str, Any] = field(default_factory=dict)

    # Server Metrics
    servers: dict[str, Any] = field(default_factory=dict)

    # Patch Metrics
    patches: dict[str, Any] = field(default_factory=dict)

    # Patch SLA Aging & Failure Operations
    sla: dict[str, Any] = field(default_factory=dict)

    # World Map Data
    map_data: list[dict] = field(default_factory=list)

    # Organization Compliance Table
    org_table: list[dict] = field(default_factory=list)

    # Slicer Items
    org_options: list[dict] = field(default_factory=list)
    location_options: list[str] = field(default_factory=list)
    os_family_options: list[str] = field(default_factory=list)
    region_options: list[str] = field(default_factory=list)

    # Raw entities (for in-memory slicing)
    organizations: list[Organization] = field(default_factory=list)
    devices_raw: list[Device] = field(default_factory=list)
    activities_raw: list[Activity] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Scoring Helpers
# ---------------------------------------------------------------------------

_WEIGHTS = {"patch": 0.50, "os_eol": 0.30, "online": 0.20}
_GREEN_THRESHOLD = 80
_AMBER_THRESHOLD = 60


def _rag(score: float) -> str:
    if score >= _GREEN_THRESHOLD:
        return "GREEN"
    if score >= _AMBER_THRESHOLD:
        return "AMBER"
    return "RED"


def _compute_overall_score(patch_pct: float, os_pct: float, online_pct: float) -> float:
    return round(
        patch_pct * _WEIGHTS["patch"]
        + os_pct * _WEIGHTS["os_eol"]
        + online_pct * _WEIGHTS["online"],
        1,
    )


# ---------------------------------------------------------------------------
# Metrics Computation for a given Device/Org Slice
# ---------------------------------------------------------------------------

def compute_dashboard_slice(
    devices: list[Device],
    organizations: list[Organization],
    activities: list[Activity],
    active_org_id: Optional[int] = None,
    active_region: Optional[str] = None,
    active_location: Optional[str] = None,
    active_os_family: Optional[str] = None,
    approaching_days: int = 180,
) -> DashboardData:
    """Computes all metrics, SLA rollups, charts data, and tables for an active multi-slicer slice."""

    # 1. Available Slicer Options (derived from total fleet)
    all_locations = sorted(list({d.location_name for d in devices if d.location_name}))
    all_os_families = ["Windows", "Linux", "macOS"]

    # 2. Apply active filtering
    filtered_devices = devices
    filtered_orgs = organizations

    # Filter by Org
    if active_org_id is not None:
        filtered_devices = [d for d in filtered_devices if d.organization_id == active_org_id]
        filtered_orgs = [o for o in filtered_orgs if o.id == active_org_id]

    # Filter by Region
    if active_region is not None and active_region not in ["Global / All", "all", None]:
        filtered_devices = [d for d in filtered_devices if d.region == active_region]
        filtered_org_ids = {d.organization_id for d in filtered_devices}
        filtered_orgs = [o for o in filtered_orgs if o.id in filtered_org_ids or o.region == active_region]

    # Filter by Location
    if active_location is not None and active_location not in ["All Locations", "all", None]:
        filtered_devices = [d for d in filtered_devices if d.location_name == active_location]
        filtered_org_ids = {d.organization_id for d in filtered_devices}
        filtered_orgs = [o for o in filtered_orgs if o.id in filtered_org_ids]

    # Filter by OS Family
    if active_os_family is not None and active_os_family not in ["All OS Families", "all", None]:
        filtered_devices = [
            d for d in filtered_devices
            if _classify_os_family(d.os.name if d.os else None) == active_os_family
        ]
        filtered_org_ids = {d.organization_id for d in filtered_devices}
        filtered_orgs = [o for o in filtered_orgs if o.id in filtered_org_ids]

    # Build org name map
    org_name_map = {o.id: o.name for o in organizations}

    # 3. Compute sub-metrics on filtered slice
    os_metrics = compute_os_metrics(filtered_devices, org_name_map=org_name_map, approaching_days=approaching_days)
    server_metrics = compute_server_metrics(filtered_devices)
    patch_metrics = compute_patch_metrics(filtered_devices, activities)
    sla_metrics = compute_patch_sla_metrics(filtered_devices, activities, org_name_map=org_name_map)

    # 4. KPI Summary
    total = len(filtered_devices)
    online = sum(1 for d in filtered_devices if d.is_online)
    online_pct = round(online / total * 100, 1) if total > 0 else 0.0

    overall_score = _compute_overall_score(
        patch_pct=patch_metrics["patch_coverage_pct"],
        os_pct=os_metrics["os_compliance_pct"],
        online_pct=online_pct,
    )

    # 5. Build Organization Summary Table
    patch_map = {r["org_id"]: r for r in patch_metrics["org_patch_table"]}
    org_table_rows = []

    for org in filtered_orgs:
        org_devs = [d for d in filtered_devices if d.organization_id == org.id]
        dev_count = len(org_devs)
        if dev_count == 0:
            continue

        onl_count = sum(1 for d in org_devs if d.is_online)
        onl_pct = round(onl_count / dev_count * 100, 1)

        p_row = patch_map.get(org.id, {})
        p_pct = p_row.get("patch_pct", 0.0)

        eol_devs = [d for d in org_devs if d.os and d.os.name and _is_eol(d.os.name)]
        os_pct = round(((dev_count - len(eol_devs)) / dev_count) * 100, 1) if dev_count > 0 else 100.0

        score = _compute_overall_score(p_pct, os_pct, onl_pct)
        rag_val = _rag(score)

        org_table_rows.append(
            {
                "org_id": org.id,
                "org_name": org.name,
                "region": org.region or "USA / North America",
                "country": org.country or "USA",
                "device_count": dev_count,
                "online_pct": onl_pct,
                "patch_pct": p_pct,
                "os_pct": os_pct,
                "eol_count": len(eol_devs),
                "compliance_score": score,
                "rag": rag_val,
            }
        )

    org_table_rows = sorted(org_table_rows, key=lambda r: r["compliance_score"])

    # 6. Build Map Data (aggregated by country)
    country_groups: dict[str, dict[str, Any]] = {}
    for row in org_table_rows:
        cc = row.get("country", "USA")
        if cc not in country_groups:
            coord = COUNTRY_COORDINATES.get(cc, {"lat": 37.09, "lon": -95.71, "name": cc, "region": row["region"]})
            country_groups[cc] = {
                "country_code": cc,
                "country_name": coord["name"],
                "region": coord["region"],
                "lat": coord["lat"],
                "lon": coord["lon"],
                "device_count": 0,
                "org_count": 0,
                "scores": [],
                "eol_count": 0,
            }
        country_groups[cc]["device_count"] += row["device_count"]
        country_groups[cc]["org_count"] += 1
        country_groups[cc]["scores"].append(row["compliance_score"])
        country_groups[cc]["eol_count"] += row.get("eol_count", 0)

    map_data = []
    for cc, g in country_groups.items():
        avg_score = round(sum(g["scores"]) / len(g["scores"]), 1) if g["scores"] else 0.0
        map_data.append(
            {
                "country_code": cc,
                "country_name": g["country_name"],
                "region": g["region"],
                "lat": g["lat"],
                "lon": g["lon"],
                "device_count": g["device_count"],
                "org_count": g["org_count"],
                "compliance_score": avg_score,
                "rag": _rag(avg_score),
                "eol_count": g["eol_count"],
            }
        )

    # Filter label construction
    filter_label_parts = []
    if active_region and active_region != "Global / All":
        filter_label_parts.append(f"Region: {active_region}")
    if active_org_id is not None:
        org_name = org_name_map.get(active_org_id, f"Org {active_org_id}")
        filter_label_parts.append(f"Org: {org_name}")
    if active_location and active_location not in ["All Locations", "all"]:
        filter_label_parts.append(f"Loc: {active_location}")
    if active_os_family and active_os_family not in ["All OS Families", "all"]:
        filter_label_parts.append(f"OS: {active_os_family}")

    filter_label = " · ".join(filter_label_parts) if filter_label_parts else "Global Overview"

    # Slicer options
    all_org_options = [{"label": "All Organizations", "value": "all"}] + [
        {"label": o.name, "value": str(o.id)} for o in organizations
    ]
    all_region_options = ["Global / All"] + list(REGION_DEFINITIONS.keys())

    return DashboardData(
        active_org_id=active_org_id,
        active_region=active_region,
        active_location=active_location,
        active_os_family=active_os_family,
        active_filter_label=filter_label,
        total_devices=total,
        online_devices=online,
        online_pct=online_pct,
        overall_compliance_score=overall_score,
        compliance_rag=_rag(overall_score),
        total_servers=server_metrics.get("server_count", 0),
        eol_risk_count=os_metrics.get("eol_count", 0),
        os=os_metrics,
        servers=server_metrics,
        patches=patch_metrics,
        sla=sla_metrics,
        map_data=map_data,
        org_table=org_table_rows,
        org_options=all_org_options,
        location_options=all_locations,
        os_family_options=all_os_families,
        region_options=all_region_options,
        organizations=organizations,
        devices_raw=devices,
        activities_raw=activities,
    )


# ---------------------------------------------------------------------------
# Metrics Aggregator Class
# ---------------------------------------------------------------------------

class MetricsAggregator:
    """
    Main aggregator with TTL caching and in-memory slicing support.
    """

    def __init__(self, client: NinjaOneClient, cache_ttl: int = 300):
        self._client = client
        self._cache = get_cache(ttl=cache_ttl)

    def get_dashboard_data(
        self,
        force_refresh: bool = False,
        active_org_id: Optional[int] = None,
        active_region: Optional[str] = None,
        active_location: Optional[str] = None,
        active_os_family: Optional[str] = None,
        approaching_days: int = 180,
    ) -> DashboardData:
        cache_key = "raw_api_payload"
        raw_bundle = self._cache.get(cache_key)

        if force_refresh or raw_bundle is None:
            console.log("[bold cyan]Fetching fresh data from NinjaOne API...[/bold cyan]")
            raw_bundle = self._fetch_raw()
            self._cache.set(cache_key, raw_bundle)

        orgs, devices, activities = raw_bundle
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

    def _fetch_raw(self) -> tuple[list[Organization], list[Device], list[Activity]]:
        orgs = get_organizations_detailed(self._client)
        devices = get_devices_detailed(self._client)
        activities = get_recent_activities(self._client, days=30)

        # Enrich organizations with geographic regions and build location dictionary
        org_geo_map = {}
        location_id_map = {}
        for org in orgs:
            cc, cname, reg, lat, lon = resolve_geo(org.name, org.description)
            org.country = cc
            org.country_code = cc
            org.region = reg
            org.latitude = lat
            org.longitude = lon
            org_geo_map[org.id] = (reg, cc, org.name)

            if org.locations:
                for loc in org.locations:
                    loc_id = loc.get("id")
                    loc_name = loc.get("name") or loc.get("description")
                    if loc_id and loc_name:
                        location_id_map[loc_id] = loc_name

        # Propagate geo and location metadata to devices
        for d in devices:
            reg, cc, default_org_name = org_geo_map.get(d.organization_id, ("USA / North America", "USA", "Corporate HQ"))
            d.region = reg
            d.country = cc

            # Assign location name if present from location_id or custom fields
            if not d.location_name:
                if d.location_id and d.location_id in location_id_map:
                    d.location_name = location_id_map[d.location_id]
                elif d.custom_fields and d.custom_fields.get("location"):
                    d.location_name = str(d.custom_fields.get("location"))
                else:
                    d.location_name = default_org_name

        return orgs, devices, activities
