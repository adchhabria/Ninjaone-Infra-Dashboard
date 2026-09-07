"""
Patch Compliance Panel — Speedometer gauge with customizable SLA thresholds.

Revised Rule:
- 0 Approved Patches: Compliant
- ≥1 Approved Patches: Non-Compliant
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
    Renders Patch Compliance gauge with configurable thresholds and compliant/non-compliant device tallies.
    """
    pct = patch_data.get("patch_coverage_pct", 0.0)
    compliant_cnt = patch_data.get("compliant_count", 0)
    non_compliant_cnt = patch_data.get("non_compliant_count", 0)
    total_devs = patch_data.get("total_devices", compliant_cnt + non_compliant_cnt)

    gauge_fig = charts.patch_gauge(pct, red_limit=red_limit, amber_limit=amber_limit, green_target=green_target)

    badge_color = "success" if pct >= green_target else "warning" if pct > red_limit else "danger"
    status_text = f"🟢 Compliant (≥{int(green_target)}%)" if pct >= green_target else f"🟡 Warning ({int(red_limit)+1}-{int(amber_limit)}%)" if pct > red_limit else f"🔴 Critical (≤{int(red_limit)}%)"

    max_approved = patch_data.get("max_approved_patches", 0)
    if max_approved == 0:
        comp_text = f"✅ Compliant (0 Approved Patches): {compliant_cnt:,}"
        non_comp_text = f"⚠️ Non-Compliant (≥1 Patches): {non_compliant_cnt:,}"
    else:
        comp_text = f"✅ Compliant (≤{max_approved} Approved Patches): {compliant_cnt:,}"
        non_comp_text = f"⚠️ Non-Compliant (>{max_approved} Patches): {non_compliant_cnt:,}"

    return dbc.Card(
        [
            dbc.CardHeader(
                dbc.Row(
                    [
                        dbc.Col(
                            html.Span([
                                html.Span("🔧", style={"marginRight": "8px"}),
                                html.Span("Patch Management & Compliance Status", style=T.FONT_SECTION_TITLE),
                                dbc.Badge(f"{pct:.1f}% Coverage", color=badge_color, className="ms-2"),
                                dbc.Badge(status_text, color="secondary", className="ms-1"),
                            ]),
                            md=6,
                        ),
                        dbc.Col(
                            html.Div(
                                [
                                    dbc.Badge(
                                        comp_text,
                                        color="success",
                                        className="me-2",
                                        style={"fontSize": "0.78rem", "padding": "5px 10px"},
                                    ),
                                    dbc.Badge(
                                        non_comp_text,
                                        color="danger" if non_compliant_cnt > 0 else "secondary",
                                        style={"fontSize": "0.78rem", "padding": "5px 10px"},
                                    ),
                                ],
                                style={"display": "flex", "flexWrap": "wrap", "justifyContent": "flex-end", "alignItems": "center"},
                            ),
                            md=6,
                        ),
                    ],
                    align="center",
                ),
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
