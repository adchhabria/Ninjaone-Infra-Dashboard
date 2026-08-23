"""
Patch Compliance Panel — Speedometer gauge with custom SLA thresholds.

Thresholds:
  - 0 - 60%:   RED
  - 61 - 84%:  AMBER
  - 85 - 100%: GREEN
"""

from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import dcc, html

from src.dashboard import charts, theme as T


def build_patch_panel(patch_data: dict) -> dbc.Card:
    """
    Renders Patch Compliance gauge with 0-60 Red, 61-84 Amber, 85+ Green thresholds.
    30-day trend removed as requested.
    """
    pct = patch_data.get("patch_coverage_pct", 0.0)
    gauge_fig = charts.patch_gauge(pct)

    badge_color = "success" if pct >= 85.0 else "warning" if pct >= 61.0 else "danger"
    status_text = "🟢 Compliant (≥85%)" if pct >= 85.0 else "🟡 Warning (61-84%)" if pct >= 61.0 else "🔴 Critical (<60%)"

    return dbc.Card(
        [
            dbc.CardHeader(
                html.Span([
                    html.Span("🔧", style={"marginRight": "8px"}),
                    html.Span("Patch Management & Compliance Status", style=T.FONT_SECTION_TITLE),
                    dbc.Badge(f"{pct:.1f}% Coverage", color=badge_color, className="ms-2"),
                    dbc.Badge(status_text, color="secondary", className="ms-1"),
                ]),
                style={"backgroundColor": T.BG_CARD, "borderBottom": f"1px solid {T.BORDER}"},
            ),
            dbc.CardBody(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                dcc.Graph(figure=gauge_fig, config={"displayModeBar": False}, style={"height": "260px"}),
                                md=12,
                            ),
                        ]
                    ),
                ],
                style={"padding": "10px"},
            ),
        ],
        style={"backgroundColor": T.BG_CARD, "border": f"1px solid {T.BORDER}", "borderRadius": "8px", "height": "100%"},
    )
