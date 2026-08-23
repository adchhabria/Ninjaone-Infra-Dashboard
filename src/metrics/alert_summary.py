"""
Alert Summary Metrics.

Aggregates NinjaOne alerts into:
- Severity breakdown (Critical / Major / Minor / Warning)
- Per-organization alert counts
- 7-day alert trend (sparkline data)
- Most recent critical alerts list
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

import pandas as pd

from src.api.models import Alert, AlertSeverity


def compute_alert_metrics(alerts: list[Alert]) -> dict[str, Any]:
    """
    Aggregate alert data for the dashboard.

    Returns:
        total_alerts:       int
        severity_counts:    {severity_label: count}
        org_alert_counts:   {org_id: count}
        trend_7d:           list[{date, count}]
        recent_critical:    list[{uid, message, device, triggered}]
        critical_count:     int
    """
    if not alerts:
        return {
            "total_alerts": 0,
            "severity_counts": {s.value: 0 for s in AlertSeverity},
            "org_alert_counts": {},
            "trend_7d": [],
            "recent_critical": [],
            "critical_count": 0,
        }

    rows = []
    for a in alerts:
        rows.append(
            {
                "uid": a.uid,
                "severity": (a.severity or AlertSeverity.NONE).value,
                "org_id": a.organization_id,
                "device": a.device_name or f"Device-{a.device_id}",
                "message": a.message or a.condition_name or "—",
                "triggered": a.triggered,
            }
        )

    df = pd.DataFrame(rows)

    # Severity breakdown
    severity_counts: dict[str, int] = defaultdict(int)
    for sev in AlertSeverity:
        severity_counts[sev.value] = 0
    for sev, cnt in df["severity"].value_counts().items():
        severity_counts[str(sev)] = int(cnt)

    # Per-org counts
    org_counts: dict[str, int] = (
        df.groupby("org_id").size().to_dict() if "org_id" in df.columns else {}
    )

    # 7-day trend
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=7)
    trend_df = df[
        df["triggered"].notna() & (pd.to_datetime(df["triggered"], utc=True) >= cutoff)
    ].copy()

    trend_7d: list[dict] = []
    if not trend_df.empty:
        trend_df["date"] = pd.to_datetime(trend_df["triggered"], utc=True).dt.date
        daily = trend_df.groupby("date").size().reset_index(name="count")
        # Fill missing days
        all_dates = pd.date_range(end=now.date(), periods=7, freq="D").date
        date_map = dict(zip(daily["date"], daily["count"]))
        trend_7d = [{"date": str(d), "count": date_map.get(d, 0)} for d in all_dates]

    # Recent critical alerts (latest 10)
    critical_df = df[df["severity"] == "CRITICAL"].copy()
    critical_count = len(critical_df)
    if not critical_df.empty:
        critical_df = critical_df.sort_values("triggered", ascending=False).head(10)
    recent_critical = critical_df[["uid", "message", "device", "triggered"]].to_dict("records")

    return {
        "total_alerts": len(alerts),
        "severity_counts": dict(severity_counts),
        "org_alert_counts": {str(k): int(v) for k, v in org_counts.items()},
        "trend_7d": trend_7d,
        "recent_critical": recent_critical,
        "critical_count": critical_count,
    }
