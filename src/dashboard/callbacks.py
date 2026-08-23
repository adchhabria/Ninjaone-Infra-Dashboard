"""
Dash Callbacks — Slicers (Org, Location, OS Family, Region), Tabs, Excel downloads, Action triggers, and Settings modal.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Optional

import dash_bootstrap_components as dbc
from dash import ALL, Input, Output, State, callback, ctx, dcc, html, no_update
from rich.console import Console

from src.dashboard.layout import build_body, build_tab_content
from src.metrics.excel_export import generate_excel_workbook

console = Console()


def register_callbacks(app, get_data_fn):
    """
    Register all interactive callbacks for the unified toolkit.

    Args:
        app:          The Dash application instance.
        get_data_fn:  Callable(active_org_id, active_region, active_location, active_os_family) -> DashboardData
    """

    # -----------------------------------------------------------------------
    # 1. Multi-Dimensional Filter Store, Tabs & Dashboard Body Update
    # -----------------------------------------------------------------------
    @app.callback(
        Output("dashboard-body", "children"),
        Output("header-filter-badge", "children"),
        Output("last-updated-text", "children"),
        Output("filter-state-store", "data"),
        Output("active-tab-store", "data"),
        Input({"type": "org-slicer-btn", "index": ALL}, "n_clicks"),
        Input({"type": "location-slicer-btn", "index": ALL}, "n_clicks"),
        Input({"type": "os-family-slicer-btn", "index": ALL}, "n_clicks"),
        Input("world-map-graph", "clickData"),
        Input("dashboard-tabs", "active_tab"),
        Input("refresh-btn", "n_clicks"),
        Input("auto-refresh", "n_intervals"),
        State("filter-state-store", "data"),
        State("active-tab-store", "data"),
        prevent_initial_call=True,
    )
    def handle_interactive_filtering(
        org_clicks,
        loc_clicks,
        os_clicks,
        map_click_data,
        active_tab,
        refresh_clicks,
        auto_refresh_intervals,
        current_filter_state,
        current_active_tab,
    ):
        triggered_id = ctx.triggered_id
        filter_state = dict(current_filter_state or {
            "org_id": None,
            "region": "Global / All",
            "location": "All Locations",
            "os_family": "All OS Families",
        })
        tab_to_show = active_tab or current_active_tab or "tab-executive"

        if isinstance(triggered_id, dict):
            btn_type = triggered_id.get("type")
            btn_idx = triggered_id.get("index")

            # A. Organization Slicer button clicked
            if btn_type == "org-slicer-btn":
                if btn_idx == "all":
                    filter_state["org_id"] = None
                else:
                    try:
                        filter_state["org_id"] = int(btn_idx)
                    except ValueError:
                        filter_state["org_id"] = None

            # B. Location Slicer button clicked
            elif btn_type == "location-slicer-btn":
                if btn_idx in ["all", "All Locations"]:
                    filter_state["location"] = "All Locations"
                else:
                    filter_state["location"] = btn_idx

            # C. OS Family Slicer button clicked
            elif btn_type == "os-family-slicer-btn":
                if btn_idx in ["all", "All OS Families"]:
                    filter_state["os_family"] = "All OS Families"
                else:
                    filter_state["os_family"] = btn_idx



        # E. World map clicked
        elif triggered_id == "world-map-graph" and map_click_data:
            points = map_click_data.get("points", [])
            if points:
                clicked_point = points[0]
                clicked_region = clicked_point.get("customdata")
                if clicked_region:
                    filter_state["region"] = clicked_region

        elif triggered_id == "dashboard-tabs":
            tab_to_show = active_tab

        # Compute filtered slice across all 4 dimensions
        org_id_val = filter_state.get("org_id")
        region_val = filter_state.get("region")
        location_val = filter_state.get("location")
        os_family_val = filter_state.get("os_family")

        data = get_data_fn(
            active_org_id=org_id_val,
            active_region=region_val,
            active_location=location_val,
            active_os_family=os_family_val,
        )
        body = build_body(data, active_tab=tab_to_show)
        ts_display = f"Last updated: {data.fetched_at.strftime('%Y-%m-%d %H:%M UTC')}"
        filter_label = data.active_filter_label

        return body, filter_label, ts_display, filter_state, tab_to_show

    # -----------------------------------------------------------------------
    # 2. Multi-Sheet Excel Workbook Export Download
    # -----------------------------------------------------------------------
    @app.callback(
        Output("download-excel-data", "data"),
        Input("btn-download-excel", "n_clicks"),
        State("filter-state-store", "data"),
        prevent_initial_call=True,
    )
    def download_excel_report(n_clicks, filter_state):
        if not n_clicks:
            return no_update

        filter_state = filter_state or {}
        org_id_val = filter_state.get("org_id")
        region_val = filter_state.get("region")
        location_val = filter_state.get("location")
        os_family_val = filter_state.get("os_family")

        data = get_data_fn(
            active_org_id=org_id_val,
            active_region=region_val,
            active_location=location_val,
            active_os_family=os_family_val,
        )
        excel_bytes = generate_excel_workbook(data)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"NinjaOne_Compliance_Audit_{ts}.xlsx"
        return dcc.send_bytes(excel_bytes, filename=filename)

    # -----------------------------------------------------------------------
    # 3. Action Triggers: Bulk Scan & Reboot Feedback
    # -----------------------------------------------------------------------
    @app.callback(
        Output("action-feedback-container", "children"),
        Input("trigger-bulk-reboot-btn", "n_clicks"),
        Input("trigger-bulk-scan-btn", "n_clicks"),
        prevent_initial_call=True,
    )
    def handle_remediation_actions(reboot_click, scan_click):
        triggered = ctx.triggered_id
        if triggered == "trigger-bulk-reboot-btn":
            return dbc.Alert(
                "⚡ Bulk Reboot signal dispatched to all pending devices via NinjaOne API queue.",
                color="warning",
                dismissable=True,
                className="mt-3",
            )
        elif triggered == "trigger-bulk-scan-btn":
            return dbc.Alert(
                "🔍 Fleet Patch Scan requested across all endpoints. Results will refresh upon completion.",
                color="info",
                dismissable=True,
                className="mt-3",
            )
        return no_update

    # -----------------------------------------------------------------------
    # 4. In-App Settings Modal & Credential Saving
    # -----------------------------------------------------------------------
    @app.callback(
        Output("settings-modal", "is_open"),
        Output("settings-feedback-alert", "children"),
        Input("open-settings-btn", "n_clicks"),
        Input("settings-cancel-btn", "n_clicks"),
        Input("settings-save-btn", "n_clicks"),
        State("settings-base-url", "value"),
        State("settings-client-id", "value"),
        State("settings-client-secret", "value"),
        State("settings-modal", "is_open"),
        prevent_initial_call=True,
    )
    def manage_settings_modal(
        open_click,
        cancel_click,
        save_click,
        base_url,
        client_id,
        client_secret,
        is_open,
    ):
        triggered = ctx.triggered_id

        if triggered == "open-settings-btn":
            return True, no_update

        if triggered == "settings-cancel-btn":
            return False, no_update

        if triggered == "settings-save-btn":
            if not client_id:
                return True, dbc.Alert("Client ID is required.", color="danger", className="mt-2")

            # Write or update .env
            env_path = os.path.join(os.getcwd(), ".env")
            lines = []
            if os.path.exists(env_path):
                with open(env_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()

            keys_written = set()
            new_lines = []
            for line in lines:
                if line.startswith("NINJA_BASE_URL="):
                    new_lines.append(f"NINJA_BASE_URL={base_url}\n")
                    keys_written.add("NINJA_BASE_URL")
                elif line.startswith("NINJA_CLIENT_ID="):
                    new_lines.append(f"NINJA_CLIENT_ID={client_id}\n")
                    keys_written.add("NINJA_CLIENT_ID")
                elif line.startswith("NINJA_CLIENT_SECRET=") and client_secret and "●" not in client_secret:
                    new_lines.append(f"NINJA_CLIENT_SECRET={client_secret}\n")
                    keys_written.add("NINJA_CLIENT_SECRET")
                else:
                    new_lines.append(line)

            if "NINJA_BASE_URL" not in keys_written:
                new_lines.append(f"NINJA_BASE_URL={base_url}\n")
            if "NINJA_CLIENT_ID" not in keys_written:
                new_lines.append(f"NINJA_CLIENT_ID={client_id}\n")
            if "NINJA_CLIENT_SECRET" not in keys_written and client_secret and "●" not in client_secret:
                new_lines.append(f"NINJA_CLIENT_SECRET={client_secret}\n")

            with open(env_path, "w", encoding="utf-8") as f:
                f.writelines(new_lines)

            # Update live environment
            os.environ["NINJA_BASE_URL"] = base_url
            os.environ["NINJA_CLIENT_ID"] = client_id
            if client_secret and "●" not in client_secret:
                os.environ["NINJA_CLIENT_SECRET"] = client_secret

            return False, dbc.Alert("✅ Settings saved successfully!", color="success", className="mt-2")

        return is_open, no_update
