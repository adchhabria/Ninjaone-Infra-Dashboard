"""
In-App Settings & NinjaOne Governance Modal.

Allows users to configure:
1. 5 NinjaOne Region Endpoints (US, US2, EU/EMEA, CA, OC/APAC) with editable custom URL.
2. API Credentials (Client ID & Client Secret).
3. Custom EOL Horizon Threshold (e.g. 90, 180, 365 days).
4. Patch Coverage Speedometer Gauge Thresholds (Red, Amber, Green).
"""

from __future__ import annotations

import os
import dash_bootstrap_components as dbc
from dash import dcc, html

from src.dashboard import theme as T


NINJA_REGIONS = [
    {"label": "United States (US / North America) — app.ninjarmm.com", "value": "https://app.ninjarmm.com"},
    {"label": "United States 2 (US2) — us2.ninjarmm.com", "value": "https://us2.ninjarmm.com"},
    {"label": "Europe, Middle East, and Africa (EU / EMEA) — eu.ninjarmm.com", "value": "https://eu.ninjarmm.com"},
    {"label": "Canada (CA) — ca.ninjarmm.com", "value": "https://ca.ninjarmm.com"},
    {"label": "Oceania / Asia-Pacific (OC / APAC) — oc.ninjarmm.com", "value": "https://oc.ninjarmm.com"},
    {"label": "Custom URL / Dedicated Domain", "value": "custom"},
]


def build_settings_modal() -> dbc.Modal:
    """Settings modal for configuring NinjaOne API credentials, regions, and governance thresholds."""
    current_url = os.getenv("NINJA_BASE_URL", "https://app.ninjarmm.com")
    current_client_id = os.getenv("NINJA_CLIENT_ID", "")
    has_secret = bool(os.getenv("NINJA_CLIENT_SECRET"))

    # Threshold defaults
    eol_threshold = int(os.getenv("EOL_THRESHOLD_DAYS", "180"))
    patch_red = float(os.getenv("PATCH_RED_LIMIT", "60.0"))
    patch_amber = float(os.getenv("PATCH_AMBER_LIMIT", "84.0"))
    patch_green = float(os.getenv("PATCH_GREEN_TARGET", "85.0"))

    # Determine initial region dropdown value
    initial_region = current_url if any(r["value"] == current_url for r in NINJA_REGIONS[:-1]) else "custom"

    return dbc.Modal(
        [
            dbc.ModalHeader(
                dbc.ModalTitle([
                    html.Span("⚙️", style={"marginRight": "8px"}),
                    html.Span("Settings & Governance Configuration"),
                ]),
                style={"backgroundColor": T.BG_CARD, "borderBottom": f"1px solid {T.BORDER}"},
            ),
            dbc.ModalBody(
                [
                    dbc.Tabs(
                        [
                            # Tab 1: NinjaOne API Connection
                            dbc.Tab(
                                [
                                    html.P(
                                        "Configure your NinjaOne API credentials. Credentials are saved locally to your .env configuration.",
                                        style={**T.FONT_BODY, "marginTop": "12px", "marginBottom": "16px"},
                                    ),
                                    dbc.Label("NinjaOne Region Preset", style=T.FONT_KPI_LABEL),
                                    dbc.Select(
                                        id="settings-region-preset",
                                        options=NINJA_REGIONS,
                                        value=initial_region,
                                        className="mb-2",
                                    ),
                                    dbc.Label("Instance Base URL (Fully Editable)", style=T.FONT_KPI_LABEL),
                                    dbc.Input(
                                        id="settings-base-url",
                                        type="text",
                                        placeholder="https://app.ninjarmm.com",
                                        value=current_url,
                                        className="mb-3",
                                    ),
                                    dbc.Label("Client ID", style=T.FONT_KPI_LABEL),
                                    dbc.Input(
                                        id="settings-client-id",
                                        type="text",
                                        placeholder="e.g. 7f8a9b0c-xxxx-xxxx-xxxx...",
                                        value=current_client_id,
                                        className="mb-3",
                                    ),
                                    dbc.Label("Client Secret", style=T.FONT_KPI_LABEL),
                                    dbc.Input(
                                        id="settings-client-secret",
                                        type="password",
                                        placeholder="●●●●●●●●●●●●●●●●" if has_secret else "Enter client secret",
                                        className="mb-3",
                                    ),
                                ],
                                label="🔌 API Connection",
                                tab_id="tab-settings-api",
                            ),

                            # Tab 2: Compliance & Governance Thresholds
                            dbc.Tab(
                                [
                                    html.P(
                                        "Customize lifecycle alerts and compliance thresholds for your organization.",
                                        style={**T.FONT_BODY, "marginTop": "12px", "marginBottom": "16px"},
                                    ),

                                    # 1. EOL Soon Threshold
                                    html.Div(
                                        [
                                            dbc.Label("📅 'Approaching EOL' Warning Horizon (Days)", style=T.FONT_KPI_LABEL),
                                            html.P("Operating systems reaching end-of-life within this time window are flagged as at-risk.",
                                                   style={"fontSize": "0.78rem", "color": T.TEXT_MUTED, "marginBottom": "8px"}),
                                            dbc.InputGroup(
                                                [
                                                    dbc.Input(
                                                        id="settings-eol-threshold",
                                                        type="number",
                                                        min=30,
                                                        max=730,
                                                        step=15,
                                                        value=eol_threshold,
                                                    ),
                                                    dbc.InputGroupText("Days (e.g. 90, 180, 365)"),
                                                ],
                                                className="mb-3",
                                            ),
                                        ]
                                    ),

                                    html.Hr(style={"borderColor": T.BORDER}),

                                    # 2. Patching Speedometer Thresholds
                                    html.Div(
                                        [
                                            dbc.Label("🎯 Patch Coverage Speedometer Gauge Thresholds (%)", style=T.FONT_KPI_LABEL),
                                            html.P("Configure the Red Alert, Amber Warning, and Green Compliance target brackets for the fleet gauge.",
                                                   style={"fontSize": "0.78rem", "color": T.TEXT_MUTED, "marginBottom": "8px"}),
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            dbc.Label("🔴 Red Limit (Max %)", style={"fontSize": "0.75rem", "color": T.RAG_RED}),
                                                            dbc.Input(
                                                                id="settings-patch-red-limit",
                                                                type="number",
                                                                min=10,
                                                                max=80,
                                                                step=5,
                                                                value=patch_red,
                                                            ),
                                                        ],
                                                        md=4,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            dbc.Label("🟡 Amber Limit (Max %)", style={"fontSize": "0.75rem", "color": T.RAG_AMBER}),
                                                            dbc.Input(
                                                                id="settings-patch-amber-limit",
                                                                type="number",
                                                                min=40,
                                                                max=95,
                                                                step=5,
                                                                value=patch_amber,
                                                            ),
                                                        ],
                                                        md=4,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            dbc.Label("🟢 Green Target (%)", style={"fontSize": "0.75rem", "color": T.RAG_GREEN}),
                                                            dbc.Input(
                                                                id="settings-patch-green-target",
                                                                type="number",
                                                                min=60,
                                                                max=100,
                                                                step=5,
                                                                value=patch_green,
                                                            ),
                                                        ],
                                                        md=4,
                                                    ),
                                                ],
                                                className="g-2 mb-3",
                                            ),
                                        ]
                                    ),
                                ],
                                label="🎯 Compliance Thresholds",
                                tab_id="tab-settings-thresholds",
                            ),
                        ],
                        active_tab="tab-settings-api",
                    ),
                    html.Div(id="settings-feedback-alert", className="mt-2"),
                ],
                style={"backgroundColor": T.BG_CARD},
            ),
            dbc.ModalFooter(
                [
                    dbc.Button("Cancel", id="settings-cancel-btn", color="secondary", outline=True, size="sm"),
                    dbc.Button("💾 Save Configuration", id="settings-save-btn", color="primary", size="sm"),
                ],
                style={"backgroundColor": T.BG_CARD, "borderTop": f"1px solid {T.BORDER}"},
            ),
        ],
        id="settings-modal",
        is_open=False,
        size="lg",
        centered=True,
    )
