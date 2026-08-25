"""
Patch Compliance Panel — Speedometer gauge with customizable SLA thresholds.

Default Thresholds:
  - 0 - 60%:   RED
  - 61 - 84%:  AMBER
  - 85 - 100%: GREEN
"""

from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import dcc, html

from src.dashboard import charts, theme as T


def build_patch_panel(
    patch_data: dict,
    red_limit: float = 60.0,
    amber_limit: float = 84.0,
    green_target: float = 85.0,
) -> dbc.Card:
    """
    Renders Patch Compliance gauge with configurable thresholds.
    """
    pct = patch_data.get("patch_coverage_pct", 0.0)
    gauge_fig = charts.patch_gauge(pct, red_limit=red_limit, amber_limit=amber_limit, green_target=green_target)

    badge_color = "success" if pct >= green_target else "warning" if pct > red_limit else "danger"
    status_text = f"🟢 Compliant (≥{int(green_target)}%)" if pct >= green_target else f"🟡 Warning ({int(red_limit)+1}-{int(amber_limit)}%)" if pct > red_limit else f"🔴 Critical (≤{int(red_limit)}%)"

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
