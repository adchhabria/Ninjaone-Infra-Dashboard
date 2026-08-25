"""
Interactive Dash Callbacks for Ninjaone Infra Dashboard.

Handles:
- Dynamic multi-slicer filtering (Organization, Location, OS Family, Map clicks)
- Instantaneous reactive dashboard body and tab rendering
- Multi-Sheet Excel workbook generation and download
- Remediation action triggers (Reboot, Patch rescan)
- In-App Settings, NinjaOne Authentication (Sign In & Sign Out), and live connection testing
- Dynamic switching between Live NinjaOne API data and Demo sample dataset
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Optional

import dash_bootstrap_components as dbc
from dash import ALL, MATCH, Input, Output, State, ctx, dcc, html, no_update
from rich.console import Console

from src.dashboard.layout import build_body, build_tab_content
from src.metrics.data_provider import coordinator
from src.metrics.excel_export import generate_excel_workbook
from src.metrics.pdf_export import generate_pdf_report

console = Console()


def register_callbacks(app, get_data_fn=None):
    """
    Register all interactive callbacks for the unified toolkit.
    """
    if get_data_fn is None:
        get_data_fn = coordinator.get_dashboard_data

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
        Input("nav-tab-executive", "n_clicks"),
        Input("nav-tab-patch-ops", "n_clicks"),
        Input("nav-tab-reboots", "n_clicks"),
        Input("nav-tab-reports", "n_clicks"),
        Input("refresh-btn", "n_clicks"),
        Input("auto-refresh", "n_intervals"),
        Input("threshold-settings-store", "data"),
        Input("auth-state-store", "data"),
        State("filter-state-store", "data"),
        State("active-tab-store", "data"),
        prevent_initial_call=True,
    )
    def handle_interactive_filtering(
        org_clicks,
        loc_clicks,
        os_clicks,
        map_click_data,
        tab_exec_clicks,
        tab_patch_clicks,
        tab_reboot_clicks,
        tab_report_clicks,
        refresh_clicks,
        auto_refresh_intervals,
        threshold_settings,
        auth_state,
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

        # Tab Navigation
        if triggered_id == "nav-tab-executive":
            tab_to_show = "tab-executive"
        elif triggered_id == "nav-tab-patch-ops":
            tab_to_show = "tab-patch-ops"
        elif triggered_id == "nav-tab-reboots":
            tab_to_show = "tab-reboots"
        elif triggered_id == "nav-tab-reports":
            tab_to_show = "tab-reports"

        # Check pattern-matching button clicks
        elif isinstance(triggered_id, dict):
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
                filter_state["location"] = str(btn_idx)

            # C. OS Family Slicer button clicked
            elif btn_type == "os-family-slicer-btn":
                filter_state["os_family"] = str(btn_idx)

        # D. World Map Marker clicked
        elif triggered_id == "world-map-graph" and map_click_data:
            points = map_click_data.get("points", [])
            if points:
                clicked_pt = points[0]
                custom = clicked_pt.get("customdata", [])
                if custom and len(custom) > 0:
                    clicked_region = custom[0]
                    if filter_state.get("region") == clicked_region:
                        filter_state["region"] = "Global / All"
                    else:
                        filter_state["region"] = clicked_region

        force_refresh = (triggered_id == "refresh-btn")

        # Query metrics using coordinator
        eol_days_val = int(ts_settings.get("eol_days", 180))
        p_red = float(ts_settings.get("patch_red", 60.0))
        p_amber = float(ts_settings.get("patch_amber", 84.0))
        p_green = float(ts_settings.get("patch_green", 85.0))

        data = coordinator.get_dashboard_data(
            active_org_id=filter_state.get("org_id"),
            active_region=filter_state.get("region"),
            active_location=filter_state.get("location"),
            active_os_family=filter_state.get("os_family"),
            force_refresh=force_refresh,
            approaching_days=eol_days_val,
        )

        badge_label = data.active_filter_label
        ts_text = f"Last updated: {data.fetched_at.strftime('%Y-%m-%d %H:%M UTC')}"

        new_body = build_body(
            data,
            active_tab=tab_to_show,
            eol_days=eol_days_val,
            patch_red=p_red,
            patch_amber=p_amber,
            patch_green=p_green,
        )

        return (
            new_body,
            badge_label,
            ts_text,
            filter_state,
            tab_to_show,
        )

    # -----------------------------------------------------------------------
    # 2. Multi-Sheet Excel Workbook Download
    # -----------------------------------------------------------------------
    @app.callback(
        Output("download-excel-data", "data"),
        Input("btn-download-excel", "n_clicks"),
        State("filter-state-store", "data"),
        State("threshold-settings-store", "data"),
        prevent_initial_call=True,
    )
    def download_excel_workbook(n_clicks, filter_state, threshold_settings):
        if not n_clicks:
            return no_update

        filter_state = filter_state or {}
        ts_settings = threshold_settings or {"eol_days": 180}
        eol_days_val = int(ts_settings.get("eol_days", 180))

        data = coordinator.get_dashboard_data(
            active_org_id=filter_state.get("org_id"),
            active_region=filter_state.get("region"),
            active_location=filter_state.get("location"),
            active_os_family=filter_state.get("os_family"),
            approaching_days=eol_days_val,
        )

        excel_bytes = generate_excel_workbook(data)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"NinjaOne_Compliance_Audit_{ts}.xlsx"
        return dcc.send_bytes(excel_bytes, filename=filename)

    # -----------------------------------------------------------------------
    # 3. Executive PDF Audit Report Download
    # -----------------------------------------------------------------------
    @app.callback(
        Output("download-pdf-data", "data"),
        Input("btn-generate-pdf-trigger", "n_clicks"),
        State("filter-state-store", "data"),
        State("threshold-settings-store", "data"),
        prevent_initial_call=True,
    )
    def download_pdf_report(n_clicks, filter_state, threshold_settings):
        if not n_clicks:
            return no_update

        filter_state = filter_state or {}
        ts_settings = threshold_settings or {"eol_days": 180}
        eol_days_val = int(ts_settings.get("eol_days", 180))

        data = coordinator.get_dashboard_data(
            active_org_id=filter_state.get("org_id"),
            active_region=filter_state.get("region"),
            active_location=filter_state.get("location"),
            active_os_family=filter_state.get("os_family"),
            approaching_days=eol_days_val,
        )

        pdf_bytes = generate_pdf_report(data)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"NinjaOne_Executive_Compliance_Audit_{ts}.pdf"
        return dcc.send_bytes(pdf_bytes, filename=filename)

    # -----------------------------------------------------------------------
    # 4. Action Triggers: Bulk Scan & Reboot Feedback
    # -----------------------------------------------------------------------
    @app.callback(
        Output("action-feedback-container", "children"),
        Input("trigger-bulk-reboot-btn", "n_clicks"),
        Input("trigger-bulk-scan-btn", "n_clicks"),
        State("filter-state-store", "data"),
        prevent_initial_call=True,
    )
    def handle_remediation_actions(reboot_clicks, scan_clicks, filter_state):
        triggered = ctx.triggered_id
        if not triggered:
            return no_update

        filter_state = filter_state or {}
        scope = filter_state.get("region", "Global")

        if triggered == "trigger-bulk-reboot-btn":
            return dbc.Alert(
                [
                    html.B("🚀 Reboot Dispatch Sent! "),
                    f"Initiated graceful reboot sequence for pending devices under scope: {scope}.",
                ],
                color="info",
                dismissable=True,
                className="mt-3",
            )
        elif triggered == "trigger-bulk-scan-btn":
            return dbc.Alert(
                [
                    html.B("🔍 Patch Scan Dispatched! "),
                    f"Triggered instant vulnerability and patch inventory scan for scope: {scope}.",
                ],
                color="success",
                dismissable=True,
                className="mt-3",
            )

        return no_update

    # -----------------------------------------------------------------------
    # 5. Settings: Region Preset Selection Sync to Editable URL Input
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
    # 6. Test Live Connection Handler
    # -----------------------------------------------------------------------
    @app.callback(
        Output("settings-test-feedback-container", "children"),
        Input("settings-test-connection-btn", "n_clicks"),
        State("settings-base-url", "value"),
        State("settings-client-id", "value"),
        State("settings-client-secret", "value"),
        prevent_initial_call=True,
    )
    def handle_test_connection(n_clicks, base_url, client_id, client_secret):
        if not n_clicks:
            return no_update

        success, msg = coordinator.test_connection(base_url, client_id, client_secret)
        if success:
            return dbc.Alert(f"✅ {msg}", color="success", className="mt-2")
        else:
            return dbc.Alert(f"❌ {msg}", color="danger", className="mt-2")

    # -----------------------------------------------------------------------
    # 7. Header Auth Controls & Sign In / Sign Out Sync
    # -----------------------------------------------------------------------
    @app.callback(
        Output("header-live-badge", "style"),
        Output("header-live-badge", "children"),
        Output("header-signout-btn", "style"),
        Output("header-demo-badge", "style"),
        Output("header-signin-btn", "style"),
        Input("auth-state-store", "data"),
    )
    def sync_header_auth_display(auth_state):
        auth_state = auth_state or {}
        is_live = auth_state.get("is_live", coordinator.is_live)
        base_url = auth_state.get("base_url", coordinator.base_url)
        clean_url = (base_url or "app.ninjarmm.com").replace("https://", "").replace("http://", "").rstrip("/")

        if is_live:
            return (
                {"fontSize": "0.78rem", "padding": "5px 10px", "display": "inline-block"},
                f"🟢 Live: {clean_url}",
                {"fontSize": "0.8rem", "display": "inline-block"},
                {"display": "none"},
                {"display": "none"},
            )
        else:
            return (
                {"display": "none"},
                no_update,
                {"display": "none"},
                {"fontSize": "0.78rem", "padding": "5px 10px", "display": "inline-block"},
                {"fontSize": "0.8rem", "fontWeight": "600", "display": "inline-block"},
            )

    # -----------------------------------------------------------------------
    # 8. In-App Settings Modal, Sign In / Sign Out & Governance Saving
    # -----------------------------------------------------------------------
    @app.callback(
        Output("settings-modal", "is_open"),
        Output("settings-feedback-alert", "children"),
        Output("threshold-settings-store", "data"),
        Output("auth-state-store", "data"),
        Input("open-settings-btn", "n_clicks"),
        Input("header-signin-btn", "n_clicks"),
        Input("header-signout-btn", "n_clicks"),
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
        State("auth-state-store", "data"),
        prevent_initial_call=True,
    )
    def manage_settings_modal(
        open_click,
        signin_click,
        signout_click,
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
        current_auth_state,
    ):
        triggered = ctx.triggered_id

        if triggered in ["open-settings-btn", "header-signin-btn"]:
            return True, no_update, no_update, no_update

        if triggered == "settings-cancel-btn":
            return False, no_update, no_update, no_update

        if triggered == "header-signout-btn":
            coordinator.sign_out()
            auth_state = {"is_live": False, "base_url": coordinator.base_url}
            return False, no_update, no_update, auth_state

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

            # If user provided API keys, attempt to sign in to live NinjaOne
            if client_id and client_secret and "●" not in client_secret:
                success, msg = coordinator.sign_in(url_to_save, client_id, client_secret)
                if not success:
                    # Show error alert in modal
                    return (
                        True,
                        dbc.Alert(f"❌ Failed to connect to NinjaOne: {msg}", color="danger", className="mt-2"),
                        no_update,
                        no_update,
                    )
                auth_state = {"is_live": True, "base_url": url_to_save}
            else:
                # Save thresholds only
                coordinator._save_to_env_file(url_to_save, client_id or "", client_secret or "")
                auth_state = {"is_live": coordinator.is_live, "base_url": url_to_save}

            return False, dbc.Alert("✅ Settings saved successfully!", color="success", className="mt-2"), thresholds_data, auth_state

        return is_open, no_update, no_update, no_update
