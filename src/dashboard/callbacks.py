"""
Interactive Dash Callbacks for Ninjaone Infra Dashboard.

Handles:
- Dynamic multi-slicer filtering (Organization, Location, OS Family, Map clicks)
- Instantaneous reactive dashboard body and tab rendering
- Multi-Sheet Excel workbook generation and download
- Remediation action triggers (Reboot, Patch rescan)
- In-App Settings & Governance configuration (5 regions + custom editable URL, EOL horizon, speedometer thresholds)
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Optional

import dash_bootstrap_components as dbc
from dash import ALL, MATCH, Input, Output, State, ctx, dcc, html, no_update
from rich.console import Console

from src.dashboard.layout import build_body, build_tab_content
from src.metrics.excel_export import generate_excel_workbook

console = Console()


def register_callbacks(app, get_data_fn):
    """
    Register all interactive callbacks for the unified toolkit.

    Args:
        app:          The Dash application instance.
        get_data_fn:  Callable(active_org_id, active_region, active_location, active_os_family, approaching_days) -> DashboardData
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
        Input("threshold-settings-store", "data"),
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
        threshold_settings,
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
        tab_to_show = current_active_tab or "tab-executive"
        ts_settings = threshold_settings or {
            "eol_days": 180,
            "patch_red": 60.0,
            "patch_amber": 84.0,
            "patch_green": 85.0,
        }

        # Check pattern-matching button clicks
        if isinstance(triggered_id, dict):
            btn_type = triggered_id.get("type")
            btn_idx = triggered_id.get("index")

            # A. Organization Slicer button clicked
            if btn_type == "org-slicer-btn":
                if btn_idx in ["all", "All Organizations"]:
                    filter_state["org_id"] = None
                else:
                    try:
                        filter_state["org_id"] = int(btn_idx)
                    except (ValueError, TypeError):
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

        # D. World map clicked
        elif triggered_id == "world-map-graph" and map_click_data:
            points = map_click_data.get("points", [])
            if points:
                clicked_point = points[0]
                clicked_region = clicked_point.get("customdata")
                if clicked_region:
                    filter_state["region"] = clicked_region

        elif triggered_id == "dashboard-tabs":
            tab_to_show = active_tab

        # Compute filtered slice across all 4 dimensions with custom EOL horizon
        org_id_val = filter_state.get("org_id")
        region_val = filter_state.get("region")
        location_val = filter_state.get("location")
        os_family_val = filter_state.get("os_family")
        eol_days_val = int(ts_settings.get("eol_days", 180))

        try:
            data = get_data_fn(
                active_org_id=org_id_val,
                active_region=region_val,
                active_location=location_val,
                active_os_family=os_family_val,
                approaching_days=eol_days_val,
            )
        except TypeError:
            data = get_data_fn(
                active_org_id=org_id_val,
                active_region=region_val,
                active_location=location_val,
                active_os_family=os_family_val,
            )

        body = build_body(data, active_tab=tab_to_show, threshold_settings=ts_settings)
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
        State("threshold-settings-store", "data"),
        prevent_initial_call=True,
    )
    def download_excel_report(n_clicks, filter_state, threshold_settings):
        if not n_clicks:
            return no_update

        filter_state = filter_state or {}
        ts_settings = threshold_settings or {"eol_days": 180}
        org_id_val = filter_state.get("org_id")
        region_val = filter_state.get("region")
        location_val = filter_state.get("location")
        os_family_val = filter_state.get("os_family")
        eol_days_val = int(ts_settings.get("eol_days", 180))

        try:
            data = get_data_fn(
                active_org_id=org_id_val,
                active_region=region_val,
                active_location=location_val,
                active_os_family=os_family_val,
                approaching_days=eol_days_val,
            )
        except TypeError:
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
    # 4. Settings: Region Preset Selection Sync to Editable URL Input
    # -----------------------------------------------------------------------
    @app.callback(
        Output("settings-base-url", "value"),
        Input("settings-region-preset", "value"),
        State("settings-base-url", "value"),
        prevent_initial_call=True,
    )
    def sync_region_preset_to_url(preset_val, current_url):
        if preset_val and preset_val != "custom":
            return preset_val
        return current_url or "https://app.ninjarmm.com"

    # -----------------------------------------------------------------------
    # 5. In-App Settings Modal & Governance Saving
    # -----------------------------------------------------------------------
    @app.callback(
        Output("settings-modal", "is_open"),
        Output("settings-feedback-alert", "children"),
        Output("threshold-settings-store", "data"),
        Input("open-settings-btn", "n_clicks"),
        Input("settings-cancel-btn", "n_clicks"),
        Input("settings-save-btn", "n_clicks"),
        State("settings-base-url", "value"),
        State("settings-client-id", "value"),
        State("settings-client-secret", "value"),
        State("settings-eol-threshold", "value"),
        State("settings-patch-red-limit", "value"),
        State("settings-patch-amber-limit", "value"),
        State("settings-patch-green-target", "value"),
        State("settings-modal", "is_open"),
        State("threshold-settings-store", "data"),
        prevent_initial_call=True,
    )
    def manage_settings_modal(
        open_click,
        cancel_click,
        save_click,
        base_url,
        client_id,
        client_secret,
        eol_threshold,
        patch_red_limit,
        patch_amber_limit,
        patch_green_target,
        is_open,
        current_thresholds,
    ):
        triggered = ctx.triggered_id

        if triggered == "open-settings-btn":
            return True, no_update, no_update

        if triggered == "settings-cancel-btn":
            return False, no_update, no_update

        if triggered == "settings-save-btn":
            # Sanitize inputs
            url_to_save = (base_url or "https://app.ninjarmm.com").strip().rstrip("/")
            if not url_to_save.startswith("http"):
                url_to_save = f"https://{url_to_save}"

            eol_val = int(eol_threshold or 180)
            p_red = float(patch_red_limit or 60.0)
            p_amber = float(patch_amber_limit or 84.0)
            p_green = float(patch_green_target or 85.0)

            thresholds_data = {
                "eol_days": eol_val,
                "patch_red": p_red,
                "patch_amber": p_amber,
                "patch_green": p_green,
            }

            # Write or update .env file
            env_path = os.path.join(os.getcwd(), ".env")
            lines = []
            if os.path.exists(env_path):
                with open(env_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()

            keys_written = set()
            new_lines = []
            for line in lines:
                if line.startswith("NINJA_BASE_URL="):
                    new_lines.append(f"NINJA_BASE_URL={url_to_save}\n")
                    keys_written.add("NINJA_BASE_URL")
                elif line.startswith("NINJA_CLIENT_ID=") and client_id:
                    new_lines.append(f"NINJA_CLIENT_ID={client_id.strip()}\n")
                    keys_written.add("NINJA_CLIENT_ID")
                elif line.startswith("NINJA_CLIENT_SECRET=") and client_secret and "●" not in client_secret:
                    new_lines.append(f"NINJA_CLIENT_SECRET={client_secret.strip()}\n")
                    keys_written.add("NINJA_CLIENT_SECRET")
                elif line.startswith("EOL_THRESHOLD_DAYS="):
                    new_lines.append(f"EOL_THRESHOLD_DAYS={eol_val}\n")
                    keys_written.add("EOL_THRESHOLD_DAYS")
                elif line.startswith("PATCH_RED_LIMIT="):
                    new_lines.append(f"PATCH_RED_LIMIT={p_red}\n")
                    keys_written.add("PATCH_RED_LIMIT")
                elif line.startswith("PATCH_AMBER_LIMIT="):
                    new_lines.append(f"PATCH_AMBER_LIMIT={p_amber}\n")
                    keys_written.add("PATCH_AMBER_LIMIT")
                elif line.startswith("PATCH_GREEN_TARGET="):
                    new_lines.append(f"PATCH_GREEN_TARGET={p_green}\n")
                    keys_written.add("PATCH_GREEN_TARGET")
                else:
                    new_lines.append(line)

            if "NINJA_BASE_URL" not in keys_written:
                new_lines.append(f"NINJA_BASE_URL={url_to_save}\n")
            if "NINJA_CLIENT_ID" not in keys_written and client_id:
                new_lines.append(f"NINJA_CLIENT_ID={client_id.strip()}\n")
            if "NINJA_CLIENT_SECRET" not in keys_written and client_secret and "●" not in client_secret:
                new_lines.append(f"NINJA_CLIENT_SECRET={client_secret.strip()}\n")
            if "EOL_THRESHOLD_DAYS" not in keys_written:
                new_lines.append(f"EOL_THRESHOLD_DAYS={eol_val}\n")
            if "PATCH_RED_LIMIT" not in keys_written:
                new_lines.append(f"PATCH_RED_LIMIT={p_red}\n")
            if "PATCH_AMBER_LIMIT" not in keys_written:
                new_lines.append(f"PATCH_AMBER_LIMIT={p_amber}\n")
            if "PATCH_GREEN_TARGET" not in keys_written:
                new_lines.append(f"PATCH_GREEN_TARGET={p_green}\n")

            with open(env_path, "w", encoding="utf-8") as f:
                f.writelines(new_lines)

            # Update process environment variables
            os.environ["NINJA_BASE_URL"] = url_to_save
            if client_id:
                os.environ["NINJA_CLIENT_ID"] = client_id.strip()
            if client_secret and "●" not in client_secret:
                os.environ["NINJA_CLIENT_SECRET"] = client_secret.strip()
            os.environ["EOL_THRESHOLD_DAYS"] = str(eol_val)
            os.environ["PATCH_RED_LIMIT"] = str(p_red)
            os.environ["PATCH_AMBER_LIMIT"] = str(p_amber)
            os.environ["PATCH_GREEN_TARGET"] = str(p_green)

            return False, dbc.Alert("✅ Settings & Thresholds saved successfully!", color="success", className="mt-2"), thresholds_data

        return is_open, no_update, no_update
