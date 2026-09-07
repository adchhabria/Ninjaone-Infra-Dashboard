"""
In-App Settings & NinjaOne Governance Modal.

Allows users to configure:
1. 🌐 Interactive Browser Login (OAuth 2.0 PKCE — No Client Secret required!).
2. 🤖 Machine-to-Machine API (Client ID + Client Secret).
3. 5 NinjaOne Region Endpoints (US, US2, EU/EMEA, CA, OC/APAC) with editable custom URL.
4. Custom EOL Horizon Threshold (e.g. 90, 180, 365 days).
5. Patch Coverage Speedometer Gauge Thresholds (Red, Amber, Green).
6. 🔄 Automatic Software Updates from GitHub Releases.
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

DEFAULT_REDIRECT_URI = "http://localhost:8050/oauth/callback"


def build_settings_modal() -> dbc.Modal:
    """Settings modal for configuring NinjaOne API credentials, regions, governance thresholds, and updates."""
    current_url = os.getenv("NINJA_BASE_URL", "https://app.ninjarmm.com")
    current_client_id = os.getenv("NINJA_CLIENT_ID", "")
    has_secret = bool(os.getenv("NINJA_CLIENT_SECRET"))
    auth_method = os.getenv("NINJA_AUTH_METHOD", "pkce")

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
                    # Hidden location for PKCE browser redirect
                    dcc.Location(id="pkce-redirect-location", refresh=True),

                    dbc.Tabs(
                        [
                            # Tab 1: NinjaOne Authentication (PKCE & Client Credentials)
                            dbc.Tab(
                                [
                                    # Auth Method Accordion / Switch
                                    dbc.Accordion(
                                        [
                                            # Option A: OAuth 2.0 PKCE Browser Login
                                            dbc.AccordionItem(
                                                [
                                                    dbc.Alert(
                                                        [
                                                            html.Div([
                                                                html.B("🌐 How to Set Up PKCE Browser Login (No Secret Required):"),
                                                                html.Ol([
                                                                    html.Li([
                                                                        "In NinjaOne console, go to ",
                                                                        html.B("Administration ➔ Apps ➔ API"),
                                                                        ".",
                                                                    ]),
                                                                    html.Li([
                                                                        "Click ",
                                                                        html.B("Add App Client"),
                                                                        " and choose ",
                                                                        html.B("Native App"),
                                                                        " or ",
                                                                        html.B("Single-Page Application (PKCE)"),
                                                                        ".",
                                                                    ]),
                                                                    html.Li([
                                                                        "Set Redirect URI to: ",
                                                                        html.Code(DEFAULT_REDIRECT_URI, style={"color": T.ACCENT_CYAN, "fontWeight": "bold"}),
                                                                    ]),
                                                                    html.Li([
                                                                        "Enable ",
                                                                        html.B("Monitoring"),
                                                                        " (and ",
                                                                        html.B("Management"),
                                                                        ") scopes.",
                                                                    ]),
                                                                    html.Li("Copy the generated Client ID and paste below."),
                                                                ], style={"marginBottom": "0", "paddingLeft": "20px"}),
                                                            ]),
                                                        ],
                                                        color="info",
                                                        className="mt-2 mb-3",
                                                        style={"fontSize": "0.82rem", "backgroundColor": "rgba(47, 129, 247, 0.12)", "border": f"1px solid {T.ACCENT_BLUE}"},
                                                    ),
                                                    dbc.Label("1. Select NinjaOne Region", style=T.FONT_KPI_LABEL),
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
                                                    dbc.Label("3. Client ID (No Client Secret Needed)", style=T.FONT_KPI_LABEL),
                                                    dbc.Input(
                                                        id="settings-client-id",
                                                        type="text",
                                                        placeholder="e.g. 7f8a9b0c-xxxx-xxxx-xxxx...",
                                                        value=current_client_id,
                                                        className="mb-3",
                                                    ),
                                                    dbc.Label("4. Redirect URI (Must Match NinjaOne App Client Exactly)", style=T.FONT_KPI_LABEL),
                                                    dbc.Input(
                                                        id="settings-redirect-uri",
                                                        type="text",
                                                        placeholder="http://localhost:8050/oauth/callback",
                                                        value=os.getenv("NINJA_REDIRECT_URI", DEFAULT_REDIRECT_URI),
                                                        className="mb-3",
                                                    ),
                                                    html.Div(
                                                        [
                                                            dbc.Button(
                                                                "🔐 Sign In with NinjaOne (Browser PKCE)",
                                                                id="settings-pkce-login-btn",
                                                                color="success",
                                                                size="md",
                                                                className="me-2",
                                                                style={"fontWeight": "600"},
                                                            ),
                                                        ],
                                                        className="mb-2",
                                                    ),
                                                    html.Div(id="settings-pkce-feedback-container"),
                                                ],
                                                title="🌐 Recommended: Interactive Browser Login (OAuth 2.0 PKCE — No Secret)",
                                                item_id="item-pkce",
                                            ),

                                            # Option B: Headless Machine-to-Machine (Client Secret)
                                            dbc.AccordionItem(
                                                [
                                                    html.P(
                                                        "For automated headless servers or background daemons using a static Client Secret.",
                                                        style={"fontSize": "0.80rem", "color": T.TEXT_MUTED, "marginTop": "8px"},
                                                    ),
                                                    dbc.Label("Client Secret", style=T.FONT_KPI_LABEL),
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
                                                title="🤖 Advanced: Machine-to-Machine (M2M Client Secret)",
                                                item_id="item-m2m",
                                            ),
                                        ],
                                        active_item="item-pkce",
                                        className="mb-3",
                                    ),
                                    html.Hr(style={"borderColor": T.BORDER, "margin": "14px 0 10px 0"}),
                                    dbc.Label("🛡️ SSL Certificate Verification", style=T.FONT_KPI_LABEL),
                                    dbc.RadioItems(
                                        id="settings-ssl-verify",
                                        options=[
                                            {"label": "🔒 Windows Native Truststore (Default)", "value": "true"},
                                            {"label": "🔓 Disable SSL Verification (Bypass Zscaler / Corporate Proxy SSL Inspection)", "value": "false"},
                                        ],
                                        value=os.getenv("NINJA_SSL_VERIFY", "true").lower(),
                                        className="mb-2",
                                        style={"fontSize": "0.82rem"},
                                    ),
                                ],
                                label="🔌 API Connection & Sign In",
                                tab_id="tab-settings-api",
                            ),

                            # Tab 2: Compliance & Governance Thresholds
                            dbc.Tab(
                                [
                                    dbc.Alert(
                                        [
                                            html.B("Criteria: "),
                                            "Extracts Approved Patch Count and Approved Software Count for each server. If approved_patch_count == 0 compliant; Otherwise it will be a Non-Compliant.",
                                        ],
                                        color="info",
                                        className="mt-3 mb-3",
                                        style={"fontSize": "0.82rem", "backgroundColor": "rgba(47, 129, 247, 0.12)", "border": f"1px solid {T.ACCENT_BLUE}"},
                                    ),

                                    # 1. Server Compliance Definition
                                    html.Div(
                                        [
                                            dbc.Label("1. Server Compliance Definition", style=T.FONT_KPI_LABEL),
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            dbc.Label("Approved Patch count for Compliance (default: 0)", style={"fontSize": "0.78rem", "color": T.TEXT_SECONDARY, "fontWeight": "600"}),
                                                            dbc.InputGroup(
                                                                [
                                                                    dbc.Input(
                                                                        id="settings-server-patch-threshold",
                                                                        type="number",
                                                                        min=0,
                                                                        max=50,
                                                                        step=1,
                                                                        value=0,
                                                                    ),
                                                                    dbc.InputGroupText("Approved Patches"),
                                                                ],
                                                                className="mb-1",
                                                            ),
                                                            html.Span(
                                                                "Servers with Approved Patch Count 0 are evaluated as Compliant; and ≥1 are evaluated as Non-Compliant devices.",
                                                                style={"fontSize": "0.74rem", "color": T.TEXT_MUTED},
                                                            ),
                                                        ],
                                                        md=12,
                                                    ),
                                                ],
                                                className="mb-3",
                                            ),
                                        ]
                                    ),

                                    html.Hr(style={"borderColor": T.BORDER}),

                                    # 2. OS Server EOL Dates (MM/DD/YYYY format)
                                    html.Div(
                                        [
                                            dbc.Label("2. OS Server EOL Dates (MM/DD/YYYY format)", style=T.FONT_KPI_LABEL),
                                            html.P("User input fields in Settings > Compliance Thresholds for server operating systems (Windows Server 2008, 2012, 2016, 2019, 2022, 2025; Ubuntu Server LTS, RHEL, CentOS, Debian).",
                                                   style={"fontSize": "0.78rem", "color": T.TEXT_MUTED, "marginBottom": "8px"}),
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            dbc.Label("Windows Server 2008 / R2", style={"fontSize": "0.75rem", "color": T.TEXT_SECONDARY}),
                                                            dbc.Input(id="settings-eol-win2008", type="text", placeholder="01/14/2020", value="01/14/2020", className="mb-2"),
                                                        ],
                                                        md=6,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            dbc.Label("Windows Server 2012 / R2", style={"fontSize": "0.75rem", "color": T.TEXT_SECONDARY}),
                                                            dbc.Input(id="settings-eol-win2012", type="text", placeholder="10/10/2023", value="10/10/2023", className="mb-2"),
                                                        ],
                                                        md=6,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            dbc.Label("Windows Server 2016", style={"fontSize": "0.75rem", "color": T.TEXT_SECONDARY}),
                                                            dbc.Input(id="settings-eol-win2016", type="text", placeholder="01/12/2027", value="01/12/2027", className="mb-2"),
                                                        ],
                                                        md=6,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            dbc.Label("Windows Server 2019", style={"fontSize": "0.75rem", "color": T.TEXT_SECONDARY}),
                                                            dbc.Input(id="settings-eol-win2019", type="text", placeholder="01/09/2029", value="01/09/2029", className="mb-2"),
                                                        ],
                                                        md=6,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            dbc.Label("Windows Server 2022", style={"fontSize": "0.75rem", "color": T.TEXT_SECONDARY}),
                                                            dbc.Input(id="settings-eol-win2022", type="text", placeholder="10/14/2031", value="10/14/2031", className="mb-2"),
                                                        ],
                                                        md=6,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            dbc.Label("Windows Server 2025", style={"fontSize": "0.75rem", "color": T.TEXT_SECONDARY}),
                                                            dbc.Input(id="settings-eol-win2025", type="text", placeholder="10/10/2034", value="10/10/2034", className="mb-2"),
                                                        ],
                                                        md=6,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            dbc.Label("Ubuntu Server LTS", style={"fontSize": "0.75rem", "color": T.TEXT_SECONDARY}),
                                                            dbc.Input(id="settings-eol-ubuntu", type="text", placeholder="04/30/2025", value="04/30/2025", className="mb-2"),
                                                        ],
                                                        md=6,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            dbc.Label("RHEL Server", style={"fontSize": "0.75rem", "color": T.TEXT_SECONDARY}),
                                                            dbc.Input(id="settings-eol-rhel", type="text", placeholder="06/30/2024", value="06/30/2024", className="mb-2"),
                                                        ],
                                                        md=6,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            dbc.Label("CentOS Server", style={"fontSize": "0.75rem", "color": T.TEXT_SECONDARY}),
                                                            dbc.Input(id="settings-eol-centos", type="text", placeholder="06/30/2024", value="06/30/2024", className="mb-2"),
                                                        ],
                                                        md=6,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            dbc.Label("Debian Server", style={"fontSize": "0.75rem", "color": T.TEXT_SECONDARY}),
                                                            dbc.Input(id="settings-eol-debian", type="text", placeholder="06/30/2026", value="06/30/2026", className="mb-2"),
                                                        ],
                                                        md=6,
                                                    ),
                                                ],
                                                className="g-2 mb-3",
                                            ),
                                        ]
                                    ),

                                    html.Hr(style={"borderColor": T.BORDER}),

                                    # 3. Approaching EOL Alert Horizon
                                    html.Div(
                                        [
                                            dbc.Label("⚠️ Approaching EOL Alert Horizon (Days)", style=T.FONT_KPI_LABEL),
                                            html.P("Configure how many days in advance devices are flagged as 'Approaching EOL'.",
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
