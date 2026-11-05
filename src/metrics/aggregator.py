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
from src.api.devices import get_devices_detailed, get_device_roles
from src.api.organizations import get_organizations_detailed
from src.api.activities import get_recent_activities
from src.api.patches import get_fleet_patch_counts
from src.api.models import Device, Organization, Activity
from src.cache.ttl_cache import get_cache
from src.metrics.os_compliance import compute_os_metrics, _is_eol, _classify_os_family
from src.metrics.server_hosting import compute_server_metrics
from src.metrics.patch_compliance import compute_patch_metrics
from src.metrics.patch_sla import compute_patch_sla_metrics

console = Console()

DEFAULT_YTD_TREND: dict[str, float] = {
    "Oct-25": 80.0,
    "Nov-25": 82.0,
    "Dec-25": 90.0,
    "Jan-26": 85.0,
    "Feb-26": 88.0,
    "Mar-26": 74.0,
    "Apr-26": 95.0,
    "May-26": 90.0,
    "Jun-26": 50.0,
    "Jul-26": 70.0,
    "Aug-26": 85.0,
    "Sep-26": 96.0,
}


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
    "US": {"name": "United States", "lat": 37.0902, "lon": -95.7129, "region": "USA / North America"},
    "GBR": {"name": "United Kingdom", "lat": 55.3781, "lon": -3.4360, "region": "EMEA / Europe"},
    "UK": {"name": "United Kingdom", "lat": 55.3781, "lon": -3.4360, "region": "EMEA / Europe"},
    "GB": {"name": "United Kingdom", "lat": 55.3781, "lon": -3.4360, "region": "EMEA / Europe"},
    "DEU": {"name": "Germany", "lat": 51.1657, "lon": 10.4515, "region": "EMEA / Europe"},
    "DE": {"name": "Germany", "lat": 51.1657, "lon": 10.4515, "region": "EMEA / Europe"},
    "SGP": {"name": "Singapore", "lat": 1.3521, "lon": 103.8198, "region": "APAC / Asia"},
    "SG": {"name": "Singapore", "lat": 1.3521, "lon": 103.8198, "region": "APAC / Asia"},
    "JPN": {"name": "Japan", "lat": 36.2048, "lon": 138.2529, "region": "APAC / Asia"},
    "JP": {"name": "Japan", "lat": 36.2048, "lon": 138.2529, "region": "APAC / Asia"},
    "IND": {"name": "India", "lat": 20.5937, "lon": 78.9629, "region": "APAC / Asia"},
    "IN": {"name": "India", "lat": 20.5937, "lon": 78.9629, "region": "APAC / Asia"},
    "AUS": {"name": "Australia", "lat": -25.2744, "lon": 133.7751, "region": "APAC / Asia"},
    "AU": {"name": "Australia", "lat": -25.2744, "lon": 133.7751, "region": "APAC / Asia"},
    "CAN": {"name": "Canada", "lat": 56.1304, "lon": -106.3468, "region": "USA / North America"},
    "CA": {"name": "Canada", "lat": 56.1304, "lon": -106.3468, "region": "USA / North America"},
    "BRA": {"name": "Brazil", "lat": -14.2350, "lon": -51.9253, "region": "Latin America"},
    "BR": {"name": "Brazil", "lat": -14.2350, "lon": -51.9253, "region": "Latin America"},
    "FRA": {"name": "France", "lat": 46.2276, "lon": 2.2137, "region": "EMEA / Europe"},
    "FR": {"name": "France", "lat": 46.2276, "lon": 2.2137, "region": "EMEA / Europe"},
    "NLD": {"name": "Netherlands", "lat": 52.1326, "lon": 5.2913, "region": "EMEA / Europe"},
    "NL": {"name": "Netherlands", "lat": 52.1326, "lon": 5.2913, "region": "EMEA / Europe"},
    "IRL": {"name": "Ireland", "lat": 53.1424, "lon": -7.6921, "region": "EMEA / Europe"},
    "IE": {"name": "Ireland", "lat": 53.1424, "lon": -7.6921, "region": "EMEA / Europe"},
    "NZL": {"name": "New Zealand", "lat": -40.9006, "lon": 174.8860, "region": "APAC / Asia"},
    "NZ": {"name": "New Zealand", "lat": -40.9006, "lon": 174.8860, "region": "APAC / Asia"},
    "HKG": {"name": "Hong Kong", "lat": 22.3193, "lon": 114.1694, "region": "APAC / Asia"},
    "HK": {"name": "Hong Kong", "lat": 22.3193, "lon": 114.1694, "region": "APAC / Asia"},
    "KOR": {"name": "South Korea", "lat": 35.9078, "lon": 127.7669, "region": "APAC / Asia"},
    "KR": {"name": "South Korea", "lat": 35.9078, "lon": 127.7669, "region": "APAC / Asia"},
}


def _resolve_device_country(d: Device, org_country: str | None = None) -> tuple[str, str, str, float, float]:
    """
    Infers Country Code, Country Name, Region, Lat, and Lon for an individual device.
    Uses device's country, location_name, or organization fallback.
    """
    # 1. Device direct country property
    candidate = str(d.country or "").strip().upper()
    if candidate in COUNTRY_COORDINATES:
        c = COUNTRY_COORDINATES[candidate]
        return candidate, c["name"], c["region"], c["lat"], c["lon"]

    # 2. Location name or description keywords
    loc = str(d.location_name or "").lower()
    if any(k in loc for k in ["sydney", "melbourne", "brisbane", "perth", "australia", "au"]):
        c = COUNTRY_COORDINATES["AUS"]
        return "AUS", c["name"], c["region"], c["lat"], c["lon"]
    if any(k in loc for k in ["tokyo", "osaka", "japan", "jp"]):
        c = COUNTRY_COORDINATES["JPN"]
        return "JPN", c["name"], c["region"], c["lat"], c["lon"]
    if any(k in loc for k in ["singapore", "sg"]):
        c = COUNTRY_COORDINATES["SGP"]
        return "SGP", c["name"], c["region"], c["lat"], c["lon"]
    if any(k in loc for k in ["india", "mumbai", "delhi", "bangalore", "in"]):
        c = COUNTRY_COORDINATES["IND"]
        return "IND", c["name"], c["region"], c["lat"], c["lon"]
    if any(k in loc for k in ["london", "uk", "manchester"]):
        c = COUNTRY_COORDINATES["GBR"]
        return "GBR", c["name"], c["region"], c["lat"], c["lon"]
    if any(k in loc for k in ["germany", "frankfurt", "berlin", "munich", "de"]):
        c = COUNTRY_COORDINATES["DEU"]
        return "DEU", c["name"], c["region"], c["lat"], c["lon"]
    if any(k in loc for k in ["canada", "toronto", "vancouver", "montreal", "ca"]):
        c = COUNTRY_COORDINATES["CAN"]
        return "CAN", c["name"], c["region"], c["lat"], c["lon"]
    if any(k in loc for k in ["brazil", "sao paulo", "rio", "br"]):
        c = COUNTRY_COORDINATES["BRA"]
        return "BRA", c["name"], c["region"], c["lat"], c["lon"]

    # 3. Fallback to org country or USA
    fallback = str(org_country or "USA").strip().upper()
    if fallback in COUNTRY_COORDINATES:
        c = COUNTRY_COORDINATES[fallback]
        return fallback, c["name"], c["region"], c["lat"], c["lon"]

    c = COUNTRY_COORDINATES["USA"]
    return "USA", c["name"], c["region"], c["lat"], c["lon"]


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
    active_os_family: Any = None
    active_roles: Any = None
    active_patch_type: str = "both"
    active_filter_label: str = "Global Overview"

    # Compliance & Speedometer Thresholds
    patch_red: float = 60.0
    patch_amber: float = 90.0
    patch_green: float = 90.0

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

    # Patch Compliance Year-to-Date (YTD) Trend
    ytd_trend: dict[str, float] = field(default_factory=dict)

    # Organization Compliance Table
    org_table: list[dict] = field(default_factory=list)

    # Slicer Items
    org_options: list[dict] = field(default_factory=list)
    location_options: list[str] = field(default_factory=list)
    os_family_options: list[str] = field(default_factory=list)
    role_options: list[str] = field(default_factory=list)
    region_options: list[str] = field(default_factory=list)
    discovered_patch_titles: list[str] = field(default_factory=list)
    compliance_included_keywords: list[str] = field(default_factory=list)
    compliance_excluded_keywords: list[str] = field(default_factory=list)
    compliance_selected_patch_titles: list[str] = field(default_factory=list)

    # Raw & Filtered entities (for in-memory slicing)
    organizations: list[Organization] = field(default_factory=list)
    devices_raw: list[Device] = field(default_factory=list)
    devices_filtered: list[Device] = field(default_factory=list)
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
    active_org_id: Any = None,
    active_region: Optional[str] = None,
    active_location: Any = None,
    active_os_family: Any = None,
    active_roles: Any = None,
    active_patch_type: str = "both",
    approaching_days: int = 180,
    custom_eol_dates: Optional[dict[str, str]] = None,
    patch_red: float = 60.0,
    patch_amber: float = 90.0,
    patch_green: float = 90.0,
    included_keywords: list[str] | None = None,
    excluded_products: list[str] | None = None,
    selected_patch_titles: list[str] | None = None,
    ytd_trend: dict[str, float] | None = None,
    raw_os_patches: list[dict] | None = None,
    raw_sw_patches: list[dict] | None = None,
) -> DashboardData:
    """Computes all metrics, SLA rollups, charts data, and tables for an active multi-slicer slice."""

    # 1. Available Slicer Options (derived from total fleet)
    detected_countries = sorted(list({
        str(d.country).strip() for d in devices
        if d.country and str(d.country).strip() not in ["all", "None", ""]
    }))
    detected_locations = sorted(list({
        str(d.location_name).strip() for d in devices
        if d.location_name and str(d.location_name).strip() not in ["all", "None", ""]
    }))
    # Combine detected countries and locations cleanly for the dropdown
    all_locations = detected_countries + [loc for loc in detected_locations if loc not in detected_countries]
    all_os_families = ["Windows", "Linux", "macOS"]
    all_role_options = sorted(list({
        str(d.device_role).strip()
        for d in devices
        if d.device_role and str(d.device_role).strip() not in ["all", "None", "", "Unknown"]
    }))
    if not all_role_options and not devices:
        all_role_options = [
            "Domain Controller",
            "Database Server",
            "Web Server",
            "File Server",
            "Application Server",
            "Backup Server",
            "General Server",
            "Workstation",
        ]

    # Pre-build org name map so Org filtering can support both IDs and Org Names safely
    org_name_map = {o.id: o.name for o in organizations}

    # 2. Apply active filtering
    filtered_devices = devices
    filtered_orgs = organizations

    # Filter by Org (supports int, list[int], string ID, or string Name without crashing)
    if active_org_id is not None:
        target_ids = set()
        target_names = set()
        items = active_org_id if isinstance(active_org_id, (list, tuple, set)) else [active_org_id]
        for x in items:
            s = str(x).strip()
            if s and s.lower() not in ["all", "all organizations", "none", ""]:
                try:
                    target_ids.add(int(s))
                except (ValueError, TypeError):
                    target_names.add(s.lower())

        if target_ids or target_names:
            filtered_devices = [
                d for d in filtered_devices
                if (d.organization_id in target_ids)
                or (org_name_map.get(d.organization_id, "").lower() in target_names)
                or any(t in org_name_map.get(d.organization_id, "").lower() for t in target_names)
            ]
            filtered_orgs = [
                o for o in filtered_orgs
                if (o.id in target_ids)
                or (o.name.lower() in target_names)
                or any(t in o.name.lower() for t in target_names)
            ]

    # Filter by Region (supports string, list, and fuzzy/substring matching like 'Europe')
    if active_region is not None:
        def _match_region(device_region: str | None, target_regions: set[str], location_name: str | None = None) -> bool:
            for t in target_regions:
                t_lower = t.lower()
                if device_region:
                    d_reg = str(device_region).lower()
                    if t_lower in d_reg or d_reg in t_lower:
                        return True
                if location_name:
                    loc_lower = str(location_name).lower()
                    if t_lower in loc_lower:
                        return True
            return False

        if isinstance(active_region, (list, tuple, set)):
            target_regs = {str(x) for x in active_region if str(x) not in ["Global / All", "all", None, ""]}
            if target_regs:
                filtered_devices = [d for d in filtered_devices if _match_region(d.region, target_regs, d.location_name)]
                filtered_org_ids = {d.organization_id for d in filtered_devices}
                filtered_orgs = [o for o in filtered_orgs if o.id in filtered_org_ids or _match_region(o.region, target_regs)]
        elif str(active_region) not in ["Global / All", "all", None, ""]:
            target_regs = {str(active_region)}
            filtered_devices = [d for d in filtered_devices if _match_region(d.region, target_regs, d.location_name)]
            filtered_org_ids = {d.organization_id for d in filtered_devices}
            filtered_orgs = [o for o in filtered_orgs if o.id in filtered_org_ids or _match_region(o.region, target_regs)]

    # Filter by Country / Location (supports Country Codes, Country Names, Regions, and Sites)
    if active_location is not None:
        items = active_location if isinstance(active_location, (list, tuple, set)) else [active_location]
        loc_set = {str(x).strip().lower() for x in items if str(x).strip().lower() not in ["all locations", "all countries", "all", "none", ""]}
        if loc_set:
            def _match_device_country_loc(dev: Device) -> bool:
                d_loc = (dev.location_name or "").lower()
                d_ctry = (dev.country or "").lower()
                d_reg = (dev.region or "").lower()
                for target in loc_set:
                    if target in d_loc or d_loc in target:
                        return True
                    if target == d_ctry or target in d_ctry or d_ctry in target:
                        return True
                    if target in d_reg or d_reg in target:
                        return True
                    # Country aliases
                    if target in ["usa", "united states", "us"] and d_ctry in ["usa", "us"]:
                        return True
                    if target in ["gbr", "uk", "united kingdom", "britain"] and d_ctry in ["gbr", "uk"]:
                        return True
                    if target in ["deu", "germany", "deutschland"] and d_ctry in ["deu", "de"]:
                        return True
                    if target in ["jpn", "japan"] and d_ctry in ["jpn", "jp"]:
                        return True
                    if target in ["ind", "india"] and d_ctry in ["ind", "in"]:
                        return True
                    if target in ["aus", "australia"] and d_ctry in ["aus", "au"]:
                        return True
                    if target in ["can", "canada"] and d_ctry in ["can", "ca"]:
                        return True
                    if target in ["bra", "brazil"] and d_ctry in ["bra", "br"]:
                        return True
                    if target in ["sgp", "singapore"] and d_ctry in ["sgp", "sg"]:
                        return True
                return False

            filtered_devices = [d for d in filtered_devices if _match_device_country_loc(d)]
            filtered_org_ids = {d.organization_id for d in filtered_devices}
            filtered_orgs = [o for o in filtered_orgs if o.id in filtered_org_ids]

    # Filter by OS Family (supports str, list[str])
    if active_os_family is not None:
        items = active_os_family if isinstance(active_os_family, (list, tuple, set)) else [active_os_family]
        os_set = {str(x).strip().lower() for x in items if str(x).strip().lower() not in ["all os families", "all", "none", ""]}
        if os_set:
            def _match_os(os_name: str | None) -> bool:
                fam = _classify_os_family(os_name).lower()
                for target in os_set:
                    if target in fam or fam in target:
                        return True
                    if "win" in target and "win" in fam:
                        return True
                    if "lin" in target and "lin" in fam:
                        return True
                    if "mac" in target and "mac" in fam:
                        return True
                return False

            filtered_devices = [
                d for d in filtered_devices
                if _match_os(d.os.name if d.os else None)
            ]
            filtered_org_ids = {d.organization_id for d in filtered_devices}
            filtered_orgs = [o for o in filtered_orgs if o.id in filtered_org_ids]

    # Filter by Device Roles (supports str, list[str])
    if active_roles is not None:
        items = active_roles if isinstance(active_roles, (list, tuple, set)) else [active_roles]
        role_set = {str(x).strip().lower() for x in items if str(x).strip().lower() not in ["all roles", "all", "none", ""]}
        if role_set:
            def _match_role(dev_role: str | None) -> bool:
                r = (dev_role or "General Server").lower()
                for target in role_set:
                    if target in r or r in target:
                        return True
                return False

            filtered_devices = [
                d for d in filtered_devices
                if _match_role(d.device_role)
            ]
            filtered_org_ids = {d.organization_id for d in filtered_devices}
            filtered_orgs = [o for o in filtered_orgs if o.id in filtered_org_ids]

    # 3. Compute sub-metrics on filtered slice
    os_metrics = compute_os_metrics(
        filtered_devices,
        org_name_map=org_name_map,
        approaching_days=approaching_days,
        custom_eol_dates=custom_eol_dates,
    )
    server_metrics = compute_server_metrics(filtered_devices, org_name_map=org_name_map)
    patch_metrics = compute_patch_metrics(
        filtered_devices,
        activities,
        org_name_map=org_name_map,
        patch_type=active_patch_type,
        included_keywords=included_keywords,
        excluded_products=excluded_products,
        selected_patch_titles=selected_patch_titles,
    )
    sla_metrics = compute_patch_sla_metrics(
        filtered_devices,
        activities,
        org_name_map=org_name_map,
        patch_type=active_patch_type,
        raw_os_patches=raw_os_patches,
        raw_sw_patches=raw_sw_patches,
    )

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

        eol_devs = [d for d in org_devs if d.os and d.os.name and _is_eol(d.os.name, custom_eol_dates=custom_eol_dates)]
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

    # 6. Build Map Data (aggregated by device country)
    country_groups: dict[str, dict[str, Any]] = {}
    eol_dev_ids = {d.id for d in eol_devs} if "eol_devs" in locals() else set()
    org_country_lookup = {o.id: o.country for o in filtered_orgs}

    for d in filtered_devices:
        org_c = org_country_lookup.get(d.organization_id)
        cc, cname, reg, lat, lon = _resolve_device_country(d, org_c)
        canonical_cc = (
            "AUS" if cc in ["AU", "AUS"]
            else "USA" if cc in ["US", "USA"]
            else "GBR" if cc in ["GB", "UK", "GBR"]
            else "DEU" if cc in ["DE", "DEU"]
            else "SGP" if cc in ["SG", "SGP"]
            else "JPN" if cc in ["JP", "JPN"]
            else "IND" if cc in ["IN", "IND"]
            else "BRA" if cc in ["BR", "BRA"]
            else "CAN" if cc in ["CA", "CAN"]
            else cc
        )

        if canonical_cc not in country_groups:
            country_groups[canonical_cc] = {
                "country_code": canonical_cc,
                "country_name": cname,
                "region": reg,
                "lat": lat,
                "lon": lon,
                "device_count": 0,
                "org_ids": set(),
                "online_count": 0,
                "eol_count": 0,
            }
        country_groups[canonical_cc]["device_count"] += 1
        country_groups[canonical_cc]["org_ids"].add(d.organization_id)
        if d.is_online:
            country_groups[canonical_cc]["online_count"] += 1
        if d.id in eol_dev_ids:
            country_groups[canonical_cc]["eol_count"] += 1

    map_data = []
    for cc, g in country_groups.items():
        dev_cnt = g["device_count"]
        onl_ratio = g["online_count"] / dev_cnt if dev_cnt > 0 else 1.0
        eol_ratio = 1.0 - (g["eol_count"] / dev_cnt) if dev_cnt > 0 else 1.0
        c_score = round((onl_ratio * 0.3 + eol_ratio * 0.3 + (patch_metrics["patch_coverage_pct"] / 100.0) * 0.4) * 100, 1)
        map_data.append(
            {
                "country_code": cc,
                "country_name": g["country_name"],
                "region": g["region"],
                "lat": g["lat"],
                "lon": g["lon"],
                "device_count": dev_cnt,
                "org_count": len(g["org_ids"]),
                "compliance_score": c_score,
                "rag": _rag(c_score),
                "eol_count": g["eol_count"],
            }
        )

    # Filter label construction - show actual selected names for all filters
    filter_label_parts = []
    if active_region and active_region not in ["Global / All", "all", "None"]:
        filter_label_parts.append(f"Region: {active_region}")

    if active_org_id:
        if isinstance(active_org_id, (list, tuple, set)):
            clean_org_ids = [x for x in active_org_id if str(x) not in ["all", "All Organizations", "None", ""]]
            if len(clean_org_ids) > 1:
                resolved_names = []
                for raw_val in clean_org_ids:
                    try:
                        resolved_names.append(org_name_map.get(int(raw_val), str(raw_val)))
                    except (ValueError, TypeError):
                        resolved_names.append(str(raw_val))
                filter_label_parts.append(f"Orgs: {', '.join(resolved_names)}")
            elif len(clean_org_ids) == 1:
                raw_val = clean_org_ids[0]
                try:
                    filter_label_parts.append(f"Org: {org_name_map.get(int(raw_val), str(raw_val))}")
                except (ValueError, TypeError):
                    filter_label_parts.append(f"Org: {raw_val}")
        elif str(active_org_id) not in ["all", "All Organizations", "None", ""]:
            try:
                filter_label_parts.append(f"Org: {org_name_map.get(int(active_org_id), f'Org {active_org_id}')}")
            except (ValueError, TypeError):
                filter_label_parts.append(f"Org: {active_org_id}")

    if active_location and active_location not in ["All Locations", "all"]:
        if isinstance(active_location, (list, tuple, set)):
            clean_locs = [str(x) for x in active_location if str(x) not in ["all", "All Locations", "All Countries", "None", ""]]
            if len(clean_locs) > 1:
                filter_label_parts.append(f"Locations: {', '.join(clean_locs)}")
            elif len(clean_locs) == 1:
                filter_label_parts.append(f"Location: {clean_locs[0]}")
        else:
            filter_label_parts.append(f"Location: {active_location}")

    if active_os_family and active_os_family not in ["All OS Families", "all"]:
        if isinstance(active_os_family, (list, tuple, set)):
            clean_os = [str(x) for x in active_os_family if str(x) not in ["all", "All OS Families", "None", ""]]
            if clean_os:
                filter_label_parts.append(f"OS: {', '.join(clean_os)}")
        else:
            filter_label_parts.append(f"OS: {active_os_family}")

    if active_roles and active_roles not in ["All Roles", "all"]:
        if isinstance(active_roles, (list, tuple, set)):
            clean_roles = [str(x) for x in active_roles if str(x) not in ["all", "All Roles", "None", ""]]
            if len(clean_roles) > 1:
                filter_label_parts.append(f"Roles: {', '.join(clean_roles)}")
            elif len(clean_roles) == 1:
                filter_label_parts.append(f"Role: {clean_roles[0]}")
        else:
            filter_label_parts.append(f"Role: {active_roles}")

    if active_patch_type and str(active_patch_type).lower() != "both":
        filter_label_parts.append(f"Patches: {str(active_patch_type).upper()}")

    filter_label = " · ".join(filter_label_parts) if filter_label_parts else "Global Overview"

    # Slicer options
    all_org_options = [{"label": "All Organizations", "value": "all"}] + [
        {"label": o.name, "value": str(o.id)} for o in organizations
    ]
    all_region_options = ["Global / All"] + list(REGION_DEFINITIONS.keys())

    all_discovered_patches = sorted(list({
        name
        for d in devices
        for name in (getattr(d, "all_uninstalled_patch_names", None) or getattr(d, "os_security_patch_names", []) or [])
        if name
    }))
    if not all_discovered_patches and not devices:
        all_discovered_patches = [
            "2024-10 Cumulative Update for Windows Server 2022 (KB5044281)",
            "2024-08 Cumulative Update for Windows 11 Version 23H2 (KB5041585)",
            "Security Update for Windows Server 2019 (KB5034441)",
            "Cumulative Update for .NET Framework 4.8.1",
            "Security Update for Microsoft SQL Server 2019",
            "Intel Network Adapter Driver Update",
        ]

    return DashboardData(
        active_org_id=active_org_id,
        active_region=active_region,
        active_location=active_location,
        active_os_family=active_os_family,
        active_roles=active_roles,
        active_patch_type=active_patch_type.lower() if isinstance(active_patch_type, str) else "both",
        active_filter_label=filter_label,
        patch_red=patch_red,
        patch_amber=patch_amber,
        patch_green=patch_green,
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
        ytd_trend=ytd_trend or DEFAULT_YTD_TREND,
        org_table=org_table_rows,
        org_options=all_org_options,
        location_options=all_locations,
        os_family_options=all_os_families,
        role_options=all_role_options,
        region_options=all_region_options,
        discovered_patch_titles=all_discovered_patches,
        compliance_included_keywords=included_keywords or ["Cumulative Update", "Security Update"],
        compliance_excluded_keywords=excluded_products or [".NET", "Office", "SQL", "Visual Studio", "Exchange", "SharePoint"],
        compliance_selected_patch_titles=selected_patch_titles or [],
        organizations=organizations,
        devices_raw=devices,
        devices_filtered=filtered_devices,
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
        import threading
        self._client = client
        self._cache = get_cache(ttl=cache_ttl)
        self._fetch_lock = threading.Lock()
        self._slice_cache: dict[tuple, DashboardData] = {}

    def get_dashboard_data(
        self,
        force_refresh: bool = False,
        active_org_id: Any = None,
        active_region: Optional[str] = None,
        active_location: Any = None,
        active_os_family: Any = None,
        active_roles: Any = None,
        active_patch_type: str = "both",
        approaching_days: int = 180,
        custom_eol_dates: Optional[dict[str, str]] = None,
        patch_red: float = 60.0,
        patch_amber: float = 90.0,
        patch_green: float = 90.0,
        included_keywords: list[str] | None = None,
        excluded_products: list[str] | None = None,
        selected_patch_titles: list[str] | None = None,
        ytd_trend: dict[str, float] | None = None,
    ) -> DashboardData:
        def _hashable(v):
            if isinstance(v, (list, tuple, set)):
                return tuple(sorted(str(x) for x in v))
            return v

        slice_key = (
            _hashable(active_org_id),
            active_region,
            _hashable(active_location),
            _hashable(active_os_family),
            _hashable(active_roles),
            active_patch_type.lower() if isinstance(active_patch_type, str) else "both",
            approaching_days,
            patch_red,
            patch_amber,
            patch_green,
            _hashable(included_keywords),
            _hashable(excluded_products),
            _hashable(selected_patch_titles),
        )

        if not force_refresh and slice_key in self._slice_cache:
            return self._slice_cache[slice_key]

        cache_key = "raw_api_payload"
        if force_refresh:
            self._cache.clear()
            self._slice_cache.clear()
            raw_bundle = None
        else:
            raw_bundle = self._cache.get(cache_key)

        if raw_bundle is None:
            # Check if stale disk cache is available for instant zero-wait startup
            stale_bundle = self._cache.get_stale(cache_key) if hasattr(self._cache, "get_stale") else None

            with self._fetch_lock:
                raw_bundle = self._cache.get(cache_key)
                if raw_bundle is None:
                    if stale_bundle is not None and not force_refresh:
                        # Return stale payload immediately; refresh asynchronously in background
                        import threading
                        def _bg_refresh():
                            with self._fetch_lock:
                                try:
                                    fresh = self._fetch_raw()
                                    self._cache.set(cache_key, fresh)
                                    self._slice_cache.clear()
                                except Exception as e:
                                    console.log(f"[yellow]Background cache refresh error: {e}[/yellow]")
                        threading.Thread(target=_bg_refresh, daemon=True).start()
                        raw_bundle = stale_bundle
                    else:
                        console.log("[bold cyan]Fetching fresh data from NinjaOne API (parallel ingestion)...[/bold cyan]")
                        raw_bundle = self._fetch_raw()
                        self._cache.set(cache_key, raw_bundle)
                        self._slice_cache.clear()

        if len(raw_bundle) >= 5:
            orgs, devices, activities, raw_os, raw_sw = raw_bundle[:5]
        else:
            orgs, devices, activities = raw_bundle[:3]
            raw_os, raw_sw = getattr(self, "_raw_os_patches", None), getattr(self, "_raw_sw_patches", None)
        computed = compute_dashboard_slice(
            devices=devices,
            organizations=orgs,
            activities=activities,
            active_org_id=active_org_id,
            active_region=active_region,
            active_location=active_location,
            active_os_family=active_os_family,
            active_roles=active_roles,
            active_patch_type=active_patch_type,
            approaching_days=approaching_days,
            custom_eol_dates=custom_eol_dates,
            patch_red=patch_red,
            patch_amber=patch_amber,
            patch_green=patch_green,
            included_keywords=included_keywords,
            excluded_products=excluded_products,
            selected_patch_titles=selected_patch_titles,
            ytd_trend=ytd_trend,
            raw_os_patches=raw_os,
            raw_sw_patches=raw_sw,
        )
        self._slice_cache[slice_key] = computed
        return computed

    def _fetch_raw(self) -> tuple[list[Organization], list[Device], list[Activity]]:
        is_mock = getattr(self._client, "_is_mock", False) or type(self._client).__name__ == "MagicMock"
        roles_map = {}
        if is_mock:
            orgs = get_organizations_detailed(self._client)
            devices = get_devices_detailed(self._client, page_size=1000)
            activities = get_recent_activities(self._client, days=30)
            patch_result = get_fleet_patch_counts(self._client)
            os_patch_counts = patch_result[0]
            sw_patch_counts = patch_result[1]
        else:
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                fut_orgs = executor.submit(get_organizations_detailed, self._client)
                fut_devices = executor.submit(get_devices_detailed, self._client, 1000)
                fut_activities = executor.submit(get_recent_activities, self._client, 30)
                fut_patches = executor.submit(get_fleet_patch_counts, self._client)
                fut_roles = executor.submit(get_device_roles, self._client)

                orgs = fut_orgs.result()
                devices = fut_devices.result()
                activities = fut_activities.result()
                patch_result = fut_patches.result()
                roles_map = fut_roles.result()
                os_patch_counts = patch_result[0]
                sw_patch_counts = patch_result[1]

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

        # Propagate geo, location, and device role metadata to devices and assign live patch counts
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

            # Map live device role from NinjaOne /v2/roles if node_role_id matches
            if d.node_role_id and roles_map and d.node_role_id in roles_map:
                d.device_role = roles_map[d.node_role_id]
            elif d.custom_fields and any(k.lower() in ["devicerole", "role", "server role", "device role"] for k in d.custom_fields):
                for k, v in d.custom_fields.items():
                    if k.lower() in ["devicerole", "role", "server role", "device role"] and v:
                        d.device_role = str(v).strip()
                        break

            # Assign real live patch counts from NinjaOne Patch Management API
            if d.id in os_patch_counts:
                d.approved_patch_count = os_patch_counts[d.id]
            elif getattr(d, "approved_patch_count", None) is None:
                d.approved_patch_count = 0

            if hasattr(patch_result, "os_sec_counts") and d.id in patch_result.os_sec_counts:
                d.os_security_patch_count = patch_result.os_sec_counts[d.id]
                d.os_security_patch_names = patch_result.os_sec_names.get(d.id, [])

            if hasattr(patch_result, "all_uninstalled_names") and d.id in patch_result.all_uninstalled_names:
                d.all_uninstalled_patch_names = patch_result.all_uninstalled_names[d.id]
            elif hasattr(patch_result, "os_sec_names") and d.id in patch_result.os_sec_names:
                d.all_uninstalled_patch_names = patch_result.os_sec_names.get(d.id, [])

            if d.id in sw_patch_counts:
                d.approved_software_count = sw_patch_counts[d.id]
            elif getattr(d, "approved_software_count", None) is None:
                d.approved_software_count = 0

        raw_os = getattr(patch_result, "raw_os_patches", []) or []
        raw_sw = getattr(patch_result, "raw_sw_patches", []) or []
        self._raw_os_patches = raw_os
        self._raw_sw_patches = raw_sw
        return orgs, devices, activities, raw_os, raw_sw
