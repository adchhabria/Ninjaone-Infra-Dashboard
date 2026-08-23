"""
In-App Settings & NinjaOne Connection Modal.

Allows users of the standalone executable / web dashboard to configure
API credentials directly from the browser UI without touching files.
"""

from __future__ import annotations

import os
import dash_bootstrap_components as dbc
from dash import dcc, html

from src.dashboard import theme as T


def build_settings_modal() -> dbc.Modal:
    """Settings modal for configuring NinjaOne API credentials."""
    current_url = os.getenv("NINJA_BASE_URL", "https://app.ninjarmm.com")
    current_client_id = os.getenv("NINJA_CLIENT_ID", "")
    has_secret = bool(os.getenv("NINJA_CLIENT_SECRET"))

    return dbc.Modal(
        [
            dbc.ModalHeader(
                dbc.ModalTitle("⚙️ NinjaOne Connection Settings"),
                style={"backgroundColor": T.BG_CARD, "borderBottom": f"1px solid {T.BORDER}"},
            ),
            dbc.ModalBody(
                [
                    html.P(
                        "Configure your NinjaOne API credentials. Credentials are saved locally to your .env configuration.",
                        style=T.FONT_BODY,
                    ),
                    dbc.Form(
                        [
                            dbc.Label("NinjaOne Instance Region URL", style=T.FONT_KPI_LABEL),
                            dbc.Select(
                                id="settings-base-url",
                                options=[
                                    {"label": "United States (https://app.ninjarmm.com)", "value": "https://app.ninjarmm.com"},
                                    {"label": "Europe (https://eu.ninjarmm.com)", "value": "https://eu.ninjarmm.com"},
                                    {"label": "Oceania / APAC (https://oc.ninjarmm.com)", "value": "https://oc.ninjarmm.com"},
                                ],
                                value=current_url,
                                className="mb-3",
                            ),
                            dbc.Label("Client ID", style=T.FONT_KPI_LABEL),
                            dbc.Input(
                                id="settings-client-id",
                                type="text",
                                placeholder="e.g. 7f8a9b0c...",
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
                            html.Div(id="settings-feedback-alert"),
                        ]
                    ),
                ],
                style={"backgroundColor": T.BG_CARD},
            ),
            dbc.ModalFooter(
                [
                    dbc.Button("Cancel", id="settings-cancel-btn", color="secondary", outline=True, size="sm"),
                    dbc.Button("💾 Save & Test Connection", id="settings-save-btn", color="primary", size="sm"),
                ],
                style={"backgroundColor": T.BG_CARD, "borderTop": f"1px solid {T.BORDER}"},
            ),
        ],
        id="settings-modal",
        is_open=False,
        centered=True,
    )
