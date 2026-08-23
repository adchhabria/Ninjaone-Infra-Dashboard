"""
OS Compliance & End-of-Life (EOL) Metrics.

Computes:
- OS family distribution (Windows / Linux / macOS / Other)
- Dedicated Windows OS build distribution (Win 11 23H2, Win 10, Server 2022, etc.)
- Dedicated Linux distribution breakdown (Ubuntu, CentOS, Debian, RHEL)
- Deep EOL analysis: Expired vs Approaching EOL vs Supported
- Days overdue calculation and risk level assignment
- Dedicated EOL audit records with organization & regional context
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

import pandas as pd

from src.api.models import Device


# ---------------------------------------------------------------------------
# EOL Date Database
# ---------------------------------------------------------------------------

_WINDOWS_EOL: dict[str, str] = {
    "Windows 7": "2020-01-14",
    "Windows 8": "2016-01-12",
    "Windows 8.1": "2023-01-10",
    "Windows 10 1507": "2017-05-09",
    "Windows 10 1511": "2017-10-10",
    "Windows 10 1607": "2018-04-10",
    "Windows 10 1703": "2018-10-09",
    "Windows 10 1709": "2019-04-09",
    "Windows 10 1803": "2019-11-12",
    "Windows 10 1809": "2020-11-10",
    "Windows 10 1903": "2020-12-08",
    "Windows 10 1909": "2021-05-11",
    "Windows 10 2004": "2021-12-14",
    "Windows 10 20H2": "2022-05-10",
    "Windows 10 21H1": "2022-12-13",
    "Windows 10 21H2": "2023-06-13",
    "Windows 10 22H2": "2025-10-14",
    "Windows Server 2003": "2015-07-14",
    "Windows Server 2008": "2020-01-14",
    "Windows Server 2008 R2": "2020-01-14",
    "Windows Server 2012": "2023-10-10",
    "Windows Server 2012 R2": "2023-10-10",
    "Windows Server 2016": "2027-01-12",
}

_LINUX_EOL: dict[str, str] = {
    "Ubuntu 14.04": "2019-04-30",
    "Ubuntu 16.04": "2021-04-30",
    "Ubuntu 18.04": "2023-04-30",
    "Ubuntu 20.04": "2025-04-30",
    "CentOS 6": "2020-11-30",
    "CentOS 7": "2024-06-30",
    "CentOS 8": "2021-12-31",
    "Debian 8": "2020-06-30",
    "Debian 9": "2022-06-30",
    "Debian 10": "2024-06-30",
}

ALL_EOL: dict[str, str] = {**_WINDOWS_EOL, **_LINUX_EOL}


def _classify_os_family(os_name: str | None) -> str:
    if not os_name:
        return "Unknown"
    name = os_name.lower()
    if "windows" in name:
        return "Windows"
    if "mac" in name or "darwin" in name or "osx" in name:
        return "macOS"
    if any(k in name for k in ["ubuntu", "debian", "centos", "rhel", "fedora", "linux"]):
        return "Linux"
    return "Other"


def _classify_windows_version(os_name: str | None, release_id: str | None) -> str:
    """Normalize Windows name to a short display version."""
    if not os_name:
        return "Unknown Windows"
    n = os_name.lower()
    rid = (release_id or "").upper()
    if "server 2025" in n:
        return "Windows Server 2025"
    if "server 2022" in n:
        return "Windows Server 2022"
    if "server 2019" in n:
        return "Windows Server 2019"
    if "server 2016" in n:
        return "Windows Server 2016"
    if "server 2012" in n:
        return "Windows Server 2012/R2"
    if "server 2008" in n:
        return "Windows Server 2008/R2"
    if "11" in n:
        return f"Windows 11 {rid}" if rid else "Windows 11"
    if "10" in n:
        return f"Windows 10 {rid}" if rid else "Windows 10"
    if "8.1" in n:
        return "Windows 8.1"
    if "7" in n:
        return "Windows 7"
    return os_name


def _classify_linux_version(os_name: str | None) -> str:
    """Normalize Linux distribution and major version."""
    if not os_name:
        return "Unknown Linux"
    n = os_name.lower()
    if "ubuntu 24" in n:
        return "Ubuntu 24.04 LTS"
    if "ubuntu 22" in n:
        return "Ubuntu 22.04 LTS"
    if "ubuntu 20" in n:
        return "Ubuntu 20.04 LTS"
    if "ubuntu 18" in n:
        return "Ubuntu 18.04 LTS"
    if "centos 7" in n:
        return "CentOS 7"
    if "centos 8" in n:
        return "CentOS 8"
    if "debian 12" in n:
        return "Debian 12"
    if "debian 11" in n:
        return "Debian 11"
    if "rhel" in n or "red hat" in n:
        return "RHEL Enterprise"
    return os_name


def _get_eol_info(os_name: str | None) -> dict[str, Any]:
    """
    Returns EOL evaluation for an OS name:
    {
        'is_eol': bool,
        'eol_date': str or None,
        'days_overdue': int,
        'status': 'Expired (EOL)' | 'Approaching EOL' | 'Supported',
        'risk_level': 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'
    }
    """
    if not os_name:
        return {
            "is_eol": False,
            "eol_date": None,
            "days_overdue": 0,
            "status": "Supported",
            "risk_level": "LOW",
        }

    today = date.today()
    for eol_key, eol_date_str in ALL_EOL.items():
        if eol_key.lower() in os_name.lower():
            try:
                eol_date = date.fromisoformat(eol_date_str)
                delta_days = (today - eol_date).days
                if delta_days > 0:
                    risk = "CRITICAL" if delta_days > 365 else "HIGH"
                    return {
                        "is_eol": True,
                        "eol_date": eol_date_str,
                        "days_overdue": delta_days,
                        "status": "Expired (EOL)",
                        "risk_level": risk,
                    }
                elif delta_days >= -180:
                    return {
                        "is_eol": False,
                        "eol_date": eol_date_str,
                        "days_overdue": delta_days,
                        "status": "Approaching EOL",
                        "risk_level": "MEDIUM",
                    }
                else:
                    return {
                        "is_eol": False,
                        "eol_date": eol_date_str,
                        "days_overdue": delta_days,
                        "status": "Supported",
                        "risk_level": "LOW",
                    }
            except ValueError:
                pass

    return {
        "is_eol": False,
        "eol_date": None,
        "days_overdue": 0,
        "status": "Supported",
        "risk_level": "LOW",
    }


def _is_eol(os_name: str | None) -> bool:
    """Return True if the OS version is past its end-of-life date."""
    return _get_eol_info(os_name)["is_eol"]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_os_metrics(
    devices: list[Device],
    org_name_map: Optional[dict[int, str]] = None,
) -> dict[str, Any]:
    """
    Compute all OS and EOL compliance metrics with separate Windows & Linux breakdowns.
    """
    org_map = org_name_map or {}
    rows = []
    for d in devices:
        os_name = d.os.name if d.os else None
        release_id = d.os.release_id if d.os else None
        family = _classify_os_family(os_name)
        eol_info = _get_eol_info(os_name)

        if family == "Windows":
            version_label = _classify_windows_version(os_name, release_id)
        elif family == "Linux":
            version_label = _classify_linux_version(os_name)
        else:
            version_label = os_name or "Unknown"

        org_name = org_map.get(d.organization_id, f"Org {d.organization_id}")
        region = d.region or "USA / North America"

        rows.append(
            {
                "id": d.id,
                "name": d.display_name or d.system_name or f"Device-{d.id}",
                "org_id": d.organization_id,
                "org_name": org_name,
                "region": region,
                "family": family,
                "version_label": version_label,
                "os_raw": os_name or "Unknown",
                "is_eol": eol_info["is_eol"],
                "eol_date": eol_info["eol_date"] or "N/A",
                "days_overdue": eol_info["days_overdue"],
                "status": eol_info["status"],
                "risk_level": eol_info["risk_level"],
            }
        )

    df = pd.DataFrame(rows)

    if df.empty:
        return {
            "family_counts": {},
            "version_counts": {},
            "windows_version_counts": {},
            "linux_version_counts": {},
            "eol_devices": [],
            "eol_table_data": [],
            "eol_status_counts": {"Supported": 0, "Approaching EOL": 0, "Expired (EOL)": 0},
            "eol_by_os": {},
            "os_compliance_pct": 100.0,
            "total_devices": 0,
            "eol_count": 0,
            "approaching_count": 0,
        }

    family_counts: dict[str, int] = df["family"].value_counts().to_dict()
    version_counts: dict[str, int] = df["version_label"].value_counts().to_dict()

    # Separate Windows & Linux counts
    win_df = df[df["family"] == "Windows"]
    windows_version_counts = win_df["version_label"].value_counts().to_dict() if not win_df.empty else {}

    linux_df = df[df["family"] == "Linux"]
    linux_version_counts = linux_df["version_label"].value_counts().to_dict() if not linux_df.empty else {}

    # EOL Status counts
    eol_status_counts = {
        "Supported": int((df["status"] == "Supported").sum()),
        "Approaching EOL": int((df["status"] == "Approaching EOL").sum()),
        "Expired (EOL)": int((df["status"] == "Expired (EOL)").sum()),
    }

    # EOL Breakdown by OS
    eol_df = df[df["status"].isin(["Expired (EOL)", "Approaching EOL"])].copy()
    eol_by_os = eol_df["version_label"].value_counts().to_dict() if not eol_df.empty else {}

    # Full EOL table data
    eol_table_data = (
        eol_df.sort_values(by=["days_overdue"], ascending=False)[
            ["id", "name", "org_name", "region", "os_raw", "eol_date", "days_overdue", "risk_level", "status"]
        ]
        .rename(columns={"os_raw": "os"})
        .to_dict("records")
        if not eol_df.empty
        else []
    )

    total = len(df)
    expired_count = int(df["is_eol"].sum())
    approaching_count = int((df["status"] == "Approaching EOL").sum())
    os_compliance_pct = round(((total - expired_count) / total) * 100, 1) if total > 0 else 100.0

    return {
        "family_counts": family_counts,
        "version_counts": version_counts,
        "windows_version_counts": windows_version_counts,
        "linux_version_counts": linux_version_counts,
        "eol_devices": eol_table_data,
        "eol_table_data": eol_table_data,
        "eol_status_counts": eol_status_counts,
        "eol_by_os": eol_by_os,
        "os_compliance_pct": os_compliance_pct,
        "total_devices": total,
        "eol_count": expired_count,
        "approaching_count": approaching_count,
    }
