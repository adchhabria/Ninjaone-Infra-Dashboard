"""
In-App Settings & NinjaOne Governance Modal.

Allows users to configure:
1. 5 NinjaOne Region Endpoints (US, US2, EU/EMEA, CA, OC/APAC) with editable custom URL.
2. API Credentials (Client ID & Client Secret) with live authentication testing.
3. Custom EOL Horizon Threshold (e.g. 90, 180, 365 days).
4. Patch Coverage Speedometer Gauge Thresholds (Red, Amber, Green).
5. 🔄 Automatic Software Updates: Check GitHub releases, download & auto-relaunch latest toolkit.
"""

from __future__ import annotations

import os
import dash_bootstrap_components as dbc
from dash import dcc, html

from src.dashboard import theme as T
from src.utils.updater import CURRENT_VERSION, GITHUB_REPO


NINJA_REGIONS = [
    {"label": "United States (US / North America) — app.ninjarmm.com", "value": "https://app.ninjarmm.com"},
    {"label": "United States 2 (US2) — us2.ninjarmm.com", "value": "https://us2.ninjarmm.com"},
    {"label": "Europe, Middle East, and Africa (EU / EMEA) — eu.ninjarmm.com", "value": "https://eu.ninjarmm.com"},
    {"label": "Canada (CA) — ca.ninjarmm.com", "value": "https://ca.ninjarmm.com"},
    {"label": "Oceania / Asia-Pacific (OC / APAC) — oc.ninjarmm.com", "value": "https://oc.ninjarmm.com"},
    {"label": "Custom URL / Dedicated Domain", "value": "custom"},
]


def build_settings_modal() -> dbc.Modal:
    """Settings modal for configuring NinjaOne API credentials, regions, governance thresholds, and updates."""
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
                    html.Span("Settings & NinjaOne Authentication"),
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
                                    dbc.Alert(
                                        [
                                            html.Div([
                                                html.B("🔐 How to Connect with NinjaOne API:"),
                                                html.Ol([
                                                    html.Li([
                                                        "Log in to your NinjaOne web console (e.g., ",
                                                        html.Code("app.ninjarmm.com", style={"color": T.ACCENT_CYAN}),
                                                        ", ",
                                                        html.Code("us2.ninjarmm.com", style={"color": T.ACCENT_CYAN}),
                                                        ", etc.).",
                                                    ]),
                                                    html.Li([
                                                        "Navigate to ",
                                                        html.B("Administration (Gear icon) ➔ Apps ➔ API"),
                                                        ".",
                                                    ]),
                                                    html.Li([
                                                        "Click ",
                                                        html.B("Add App Client"),
                                                        " and choose ",
                                                        html.B("Machine-to-Machine (Client Credentials)"),
                                                        ".",
                                                    ]),
                                                    html.Li([
                                                        "Enable the ",
                                                        html.B("Monitoring"),
                                                        " (and ",
                                                        html.B("Management"),
                                                        ") scopes.",
                                                    ]),
                                                    html.Li("Copy the generated Client ID and Client Secret and paste below."),
                                                ], style={"marginBottom": "0", "paddingLeft": "20px"}),
                                            ]),
                                        ],
                                        color="info",
                                        className="mt-2 mb-3",
                                        style={"fontSize": "0.82rem", "backgroundColor": "rgba(47, 129, 247, 0.12)", "border": f"1px solid {T.ACCENT_BLUE}"},
                                    ),
                                    dbc.Label("1. Select NinjaOne Region Preset", style=T.FONT_KPI_LABEL),
                                    dbc.Select(
                                        id="settings-region-preset",
                                        options=NINJA_REGIONS,
                                        value=initial_region,
                                        className="mb-2",
                                    ),
                                    dbc.Label("2. Instance Base URL (Editable)", style=T.FONT_KPI_LABEL),
                                    dbc.Input(
                                        id="settings-base-url",
                                        type="text",
                                        placeholder="https://app.ninjarmm.com",
                                        value=current_url,
                                        className="mb-3",
                                    ),
                                    dbc.Label("3. Client ID", style=T.FONT_KPI_LABEL),
                                    dbc.Input(
                                        id="settings-client-id",
                                        type="text",
                                        placeholder="e.g. 7f8a9b0c-xxxx-xxxx-xxxx...",
                                        value=current_client_id,
                                        className="mb-3",
                                    ),
                                    dbc.Label("4. Client Secret", style=T.FONT_KPI_LABEL),
                                    dbc.Input(
                                        id="settings-client-secret",
                                        type="password",
                                        placeholder="●●●●●●●●●●●●●●●●" if has_secret else "Enter client secret",
                                        className="mb-3",
                                    ),
                                    html.Div(
                                        [
                                            dbc.Button(
                                                "⚡ Test API Connection",
                                                id="settings-test-connection-btn",
                                                color="info",
                                                outline=True,
                                                size="sm",
                                                className="me-2",
                                            ),
                                        ],
                                        className="mb-2",
                                    ),
                                    html.Div(id="settings-test-feedback-container"),
                                ],
                                label="🔌 API Connection & Sign In",
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
                                                                min=30,
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

                            # Tab 3: Software Updates & Version Management
                            dbc.Tab(
                                [
                                    html.Div(
                                        [
                                            dbc.Card(
                                                dbc.CardBody(
                                                    [
                                                        html.Div(
                                                            [
                                                                html.Div(
                                                                    [
                                                                        html.Span("📦", style={"fontSize": "1.8rem", "marginRight": "12px"}),
                                                                        html.Div(
                                                                            [
                                                                                html.H6("NinjaOne Infra Dashboard Toolkit", style={"margin": "0", "fontWeight": "700", "color": T.TEXT_PRIMARY}),
                                                                                html.Span(f"Current Installed Version: v{CURRENT_VERSION}", style={"fontSize": "0.82rem", "color": T.ACCENT_CYAN, "fontWeight": "600"}),
                                                                            ]
                                                                        ),
                                                                    ],
                                                                    style={"display": "flex", "alignItems": "center"},
                                                                ),
                                                                dbc.Badge("Release Channel: GitHub Stable", color="dark", style={"fontSize": "0.75rem", "borderColor": T.BORDER, "border": f"1px solid {T.BORDER}"}),
                                                            ],
                                                            style={"display": "flex", "alignItems": "center", "justifyContent": "space-between"},
                                                        ),
                                                        html.Hr(style={"borderColor": T.BORDER, "margin": "12px 0"}),
                                                        html.P(
                                                            "Check for new releases, feature updates, bug fixes, and security patches directly from the official repository.",
                                                            style={"fontSize": "0.80rem", "color": T.TEXT_MUTED, "marginBottom": "12px"},
                                                        ),
                                                        html.Div(
                                                            [
                                                                dbc.Button(
                                                                    "🔄 Check for Updates",
                                                                    id="settings-check-update-btn",
                                                                    color="primary",
                                                                    size="sm",
                                                                    className="me-2",
                                                                    style={"fontWeight": "600"},
                                                                ),
                                                                html.A(
                                                                    "📂 View Releases on GitHub ↗",
                                                                    href=f"https://github.com/{GITHUB_REPO}/releases",
                                                                    target="_blank",
                                                                    style={"fontSize": "0.80rem", "color": T.ACCENT_BLUE, "textDecoration": "none", "marginLeft": "10px"},
                                                                ),
                                                            ],
                                                            style={"display": "flex", "alignItems": "center"},
                                                        ),
                                                        # Hidden store for payload URL
                                                        dcc.Store(id="update-download-url-store"),
                                                        html.Div(id="settings-update-feedback-container", className="mt-3"),
                                                    ]
                                                ),
                                                style={"backgroundColor": T.BG_CARD, "border": f"1px solid {T.BORDER}", "marginTop": "14px"},
                                            ),
                                        ]
                                    ),
                                ],
                                label="🔄 Software Updates",
                                tab_id="tab-settings-updates",
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
                    dbc.Button("💾 Save & Connect Live API", id="settings-save-btn", color="primary", size="sm"),
                ],
                style={"backgroundColor": T.BG_CARD, "borderTop": f"1px solid {T.BORDER}"},
            ),
        ],
        id="settings-modal",
        is_open=False,
        size="lg",
        centered=True,
    )
