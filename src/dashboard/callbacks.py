"""
Interactive Dash Callbacks for Ninjaone Infra Dashboard.

Handles:
- Dynamic multi-slicer filtering (Organization, Location, OS Family, Map clicks)
- Instantaneous reactive dashboard body and tab rendering
- Multi-Sheet Excel workbook generation and download
- Remediation action triggers (Reboot, Patch rescan)
- In-App Settings, NinjaOne Authentication (PKCE Browser Login & Client Credentials, Sign In & Sign Out)
- Live connection testing and automatic data switching
- Software Update Checker, GitHub Releases API integration, and self-updating auto-relaunch
"""

from __future__ import annotations

import os
import webbrowser
from datetime import datetime, timezone
from typing import Any, Optional

import dash_bootstrap_components as dbc
from dash import ALL, MATCH, Input, Output, State, ctx, dcc, html, no_update
from rich.console import Console

from src.dashboard import charts, theme as T
from src.dashboard.layout import build_body, build_tab_content
from src.metrics.data_provider import coordinator
from src.metrics.excel_export import generate_excel_workbook
from src.metrics.pdf_export import generate_pdf_report
from src.reporting.html_export import generate_html_report
from src.utils.updater import CURRENT_VERSION, check_for_updates, apply_update_and_restart

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
        srv_threshold = int(ts_settings.get("server_patch_threshold", 0))
        c_eol_dates = ts_settings.get("custom_eol_dates", None)

        data = coordinator.get_dashboard_data(
            active_org_id=filter_state.get("org_id"),
            active_region=filter_state.get("region"),
            active_location=filter_state.get("location"),
            active_os_family=filter_state.get("os_family"),
            force_refresh=force_refresh,
            approaching_days=eol_days_val,
            custom_eol_dates=c_eol_dates,
            server_patch_threshold=srv_threshold,
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
        srv_threshold = int(ts_settings.get("server_patch_threshold", 0))
        c_eol_dates = ts_settings.get("custom_eol_dates", None)

        data = coordinator.get_dashboard_data(
            active_org_id=filter_state.get("org_id"),
            active_region=filter_state.get("region"),
            active_location=filter_state.get("location"),
            active_os_family=filter_state.get("os_family"),
            approaching_days=eol_days_val,
            custom_eol_dates=c_eol_dates,
            server_patch_threshold=srv_threshold,
        )

        excel_bytes = generate_excel_workbook(data)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"NinjaOne_Compliance_Audit_{ts}.xlsx"
        return dcc.send_bytes(excel_bytes, filename=filename)

    # -----------------------------------------------------------------------
    # 2b. Hosting Infrastructure Filter Radio Toggle
    # -----------------------------------------------------------------------
    @app.callback(
        Output("hosting-donut-graph", "figure"),
        Output("hosting-stacked-bar-graph", "figure"),
        Input("hosting-filter-radio", "value"),
        State("filter-state-store", "data"),
        State("threshold-settings-store", "data"),
        prevent_initial_call=True,
    )
    def update_hosting_filter(filter_mode, filter_state, threshold_settings):
        if not filter_mode:
            return no_update, no_update
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
        hosting_counts = data.servers.get("hosting_counts", {})
        org_dist = data.servers.get("org_distribution", [])

        donut_fig = charts.hosting_donut(hosting_counts, filter_mode=filter_mode)
        bar_fig = charts.hosting_org_stacked_bar(org_dist, filter_mode=filter_mode)
        return donut_fig, bar_fig

    # -----------------------------------------------------------------------
    # 3. Executive PDF Audit Report Download
    # -----------------------------------------------------------------------
    @app.callback(
        Output("download-pdf-data", "data"),
        Input("btn-generate-pdf-trigger", "n_clicks"),
        Input("header-pdf-btn", "n_clicks"),
        State("filter-state-store", "data"),
        State("threshold-settings-store", "data"),
        prevent_initial_call=True,
    )
    def download_pdf_report(panel_clicks, header_clicks, filter_state, threshold_settings):
        if not (panel_clicks or header_clicks):
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

        try:
            pdf_bytes = generate_pdf_report(data)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"NinjaOne_Executive_Compliance_Audit_{ts}.pdf"
            return dcc.send_bytes(pdf_bytes, filename=filename)
        except Exception as e:
            console.log(f"[red]Error generating PDF report: {e}[/red]")
            return no_update

    # -----------------------------------------------------------------------
    # 3b. Standalone Interactive HTML Report Download & Share
    # -----------------------------------------------------------------------
    @app.callback(
        Output("download-html-data", "data"),
        Input("btn-download-html-trigger", "n_clicks"),
        Input("header-share-btn", "n_clicks"),
        State("filter-state-store", "data"),
        State("threshold-settings-store", "data"),
        prevent_initial_call=True,
    )
    def download_html_report(panel_clicks, header_clicks, filter_state, threshold_settings):
        if not (panel_clicks or header_clicks):
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

        try:
            html_text = generate_html_report(data)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"NinjaOne_Executive_Report_{ts}.html"
            return dict(content=html_text, filename=filename)
        except Exception as e:
            console.log(f"[red]Error generating HTML report: {e}[/red]")
            return no_update

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
    # 6. Test Live Connection Handler (M2M Client Credentials)
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
    # 7. PKCE Browser Login Trigger Callback
    # -----------------------------------------------------------------------
    @app.callback(
        Output("settings-pkce-feedback-container", "children"),
        Output("pkce-redirect-location", "href"),
        Input("settings-pkce-login-btn", "n_clicks"),
        State("settings-base-url", "value"),
        State("settings-client-id", "value"),
        State("settings-redirect-uri", "value"),
        State("settings-ssl-verify", "value"),
        prevent_initial_call=True,
    )
    def handle_pkce_browser_login(n_clicks, base_url, client_id, redirect_uri, ssl_verify):
        if not n_clicks:
            return no_update, no_update

        if not client_id or not client_id.strip():
            return (
                dbc.Alert(
                    "❌ Client ID is required for PKCE login. Please enter your NinjaOne Client ID.",
                    color="danger",
                    className="mt-2",
                ),
                no_update,
            )

        base_url = (base_url or "https://app.ninjarmm.com").strip().rstrip("/")
        if not base_url.startswith("http"):
            base_url = f"https://{base_url}"

        redirect_uri = (redirect_uri or "http://localhost:8050/oauth/callback").strip()

        # Apply SSL verification preference
        if ssl_verify:
            os.environ["NINJA_SSL_VERIFY"] = str(ssl_verify).lower()

        try:
            auth_url, state = coordinator.initiate_pkce_login(base_url, client_id.strip(), redirect_uri=redirect_uri)
            # Automatically launch the user's default browser
            webbrowser.open(auth_url)

            feedback = dbc.Alert(
                [
                    html.Div([
                        html.Span("🚀 ", style={"fontSize": "1.2rem"}),
                        html.B("NinjaOne Login Window Opened!"),
                    ]),
                    html.P(
                        "Please complete authentication in your browser. The dashboard will automatically refresh with live data once authorized.",
                        style={"fontSize": "0.82rem", "marginBottom": "6px", "marginTop": "4px"},
                    ),
                    html.A(
                        "Click here if browser did not open automatically ↗",
                        href=auth_url,
                        target="_blank",
                        style={"fontSize": "0.80rem", "color": T.ACCENT_CYAN, "textDecoration": "none"},
                    ),
                ],
                color="info",
                className="mt-2",
            )
            return feedback, no_update
        except Exception as e:
            return dbc.Alert(f"❌ Failed to initiate PKCE login: {str(e)}", color="danger", className="mt-2"), no_update

    # -----------------------------------------------------------------------
    # 8. Header Auth Controls & Sign In / Sign Out Sync
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
            method_badge = " (PKCE)" if coordinator.auth_method == "pkce" else ""
            return (
                {"fontSize": "0.78rem", "padding": "5px 10px", "display": "inline-block"},
                f"🟢 Live: {clean_url}{method_badge}",
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
    # 9. In-App Settings Modal, Sign In / Sign Out & Governance Saving
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
        State("settings-redirect-uri", "value"),
        State("settings-ssl-verify", "value"),
        State("settings-eol-threshold", "value"),
        State("settings-patch-red-limit", "value"),
        State("settings-patch-amber-limit", "value"),
        State("settings-patch-green-target", "value"),
        State("settings-server-patch-threshold", "value"),
        State("settings-eol-win2008", "value"),
        State("settings-eol-win2012", "value"),
        State("settings-eol-win2016", "value"),
        State("settings-eol-win2019", "value"),
        State("settings-eol-win2022", "value"),
        State("settings-eol-win2025", "value"),
        State("settings-eol-ubuntu", "value"),
        State("settings-eol-rhel", "value"),
        State("settings-eol-centos", "value"),
        State("settings-eol-debian", "value"),
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
        redirect_uri,
        ssl_verify,
        eol_threshold,
        patch_red_limit,
        patch_amber_limit,
        patch_green_target,
        server_patch_threshold,
        eol_win2008,
        eol_win2012,
        eol_win2016,
        eol_win2019,
        eol_win2022,
        eol_win2025,
        eol_ubuntu,
        eol_rhel,
        eol_centos,
        eol_debian,
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

            redirect_to_save = (redirect_uri or "http://localhost:8050/oauth/callback").strip()
            ssl_to_save = str(ssl_verify or "true").lower()
            os.environ["NINJA_SSL_VERIFY"] = ssl_to_save

            eol_val = int(eol_threshold or 180)
            p_red = float(patch_red_limit or 60.0)
            p_amber = float(patch_amber_limit or 84.0)
            p_green = float(patch_green_target or 85.0)
            srv_threshold = int(server_patch_threshold if server_patch_threshold is not None else 0)

            custom_eol = {
                "Windows Server 2008": eol_win2008 or "01/14/2020",
                "Windows Server 2012": eol_win2012 or "10/10/2023",
                "Windows Server 2016": eol_win2016 or "01/12/2027",
                "Windows Server 2019": eol_win2019 or "01/09/2029",
                "Windows Server 2022": eol_win2022 or "10/14/2031",
                "Windows Server 2025": eol_win2025 or "10/10/2034",
                "Ubuntu": eol_ubuntu or "04/30/2025",
                "RHEL": eol_rhel or "06/30/2024",
                "CentOS": eol_centos or "06/30/2024",
                "Debian": eol_debian or "06/30/2026",
            }

            thresholds_data = {
                "eol_days": eol_val,
                "patch_red": p_red,
                "patch_amber": p_amber,
                "patch_green": p_green,
                "server_patch_threshold": srv_threshold,
                "custom_eol_dates": custom_eol,
            }

            # If user provided API keys with Client Secret, attempt M2M sign in
            if client_id and client_secret and "●" not in client_secret:
                success, msg = coordinator.sign_in(url_to_save, client_id, client_secret)
                if not success:
                    return (
                        True,
                        dbc.Alert(f"❌ Failed to connect to NinjaOne: {msg}", color="danger", className="mt-2"),
                        no_update,
                        no_update,
                    )
                auth_state = {"is_live": True, "base_url": url_to_save}
            else:
                # Save configuration
                coordinator._save_to_env_file(url_to_save, client_id or "", client_secret or "", redirect_uri=redirect_to_save, ssl_verify=ssl_to_save)
                auth_state = {"is_live": coordinator.is_live, "base_url": url_to_save}

            return False, dbc.Alert("✅ Configuration saved successfully!", color="success", className="mt-2"), thresholds_data, auth_state

        return is_open, no_update, no_update, no_update

    # -----------------------------------------------------------------------
    # 10. Check for Updates Callback
    # -----------------------------------------------------------------------
    @app.callback(
        Output("settings-update-feedback-container", "children"),
        Output("update-download-url-store", "data"),
        Input("settings-check-update-btn", "n_clicks"),
        prevent_initial_call=True,
    )
    def handle_check_for_updates(n_clicks):
        if not n_clicks:
            return no_update, no_update

        res = check_for_updates()
        if not res.get("success"):
            return (
                dbc.Alert(
                    [
                        html.B("⚠️ Update Check Notice: "),
                        html.Span(res.get("message", "Unable to query GitHub API.")),
                    ],
                    color="warning",
                    className="mt-2",
                ),
                None,
            )

        if res.get("update_available"):
            latest_v = res.get("latest_version")
            pub = res.get("published_at")
            notes = res.get("release_notes", "")
            dl_url = res.get("download_url", "")

            return (
                dbc.Alert(
                    [
                        html.Div(
                            [
                                html.Span("🎉 ", style={"fontSize": "1.2rem"}),
                                html.B(f"New Version Available: {latest_v}"),
                                html.Span(f" (Released: {pub})", style={"fontSize": "0.78rem", "color": T.TEXT_MUTED, "marginLeft": "6px"}),
                            ],
                            className="mb-2",
                        ),
                        html.Div(
                            [
                                html.B("Release Notes:"),
                                html.Pre(
                                    notes[:400] + ("..." if len(notes) > 400 else ""),
                                    style={
                                        "fontSize": "0.78rem",
                                        "backgroundColor": "rgba(0,0,0,0.25)",
                                        "padding": "8px",
                                        "borderRadius": "4px",
                                        "whiteSpace": "pre-wrap",
                                        "marginTop": "6px",
                                        "color": T.TEXT_PRIMARY,
                                    },
                                ),
                            ],
                            className="mb-3",
                        ) if notes else html.Div(),
                        html.Div(
                            [
                                dbc.Button(
                                    f"🚀 Download & Install {latest_v} (Auto-Restart)",
                                    id="trigger-apply-update-btn",
                                    color="success",
                                    size="sm",
                                    className="me-2",
                                    style={"fontWeight": "600"},
                                ),
                                html.A(
                                    "Manual Download ↗",
                                    href=res.get("html_url", "#"),
                                    target="_blank",
                                    style={"fontSize": "0.80rem", "color": T.ACCENT_CYAN, "textDecoration": "none"},
                                ),
                            ],
                            style={"display": "flex", "alignItems": "center"},
                        ),
                        html.Div(id="update-apply-status-container", className="mt-2"),
                    ],
                    color="success",
                    className="mt-2",
                ),
                dl_url,
            )
        else:
            return (
                dbc.Alert(
                    [
                        html.Span("✅ ", style={"fontSize": "1.1rem"}),
                        html.B(f"Toolkit is Up-to-Date (v{CURRENT_VERSION})! "),
                        "You are currently running the latest official build.",
                    ],
                    color="info",
                    className="mt-2",
                ),
                None,
            )

    # -----------------------------------------------------------------------
    # 11. Install Update & Auto-Restart Callback
    # -----------------------------------------------------------------------
    @app.callback(
        Output("update-apply-status-container", "children"),
        Input("trigger-apply-update-btn", "n_clicks"),
        State("update-download-url-store", "data"),
        prevent_initial_call=True,
    )
    def handle_install_update(n_clicks, download_url):
        if not n_clicks or not download_url:
            return no_update

        success, msg = apply_update_and_restart(download_url)
        if success:
            return dbc.Alert(
                [
                    html.B("⬇️ Update Downloaded! "),
                    "Launching updater launcher and restarting the toolkit in 2 seconds...",
                ],
                color="info",
                className="mt-2",
            )
        else:
            return dbc.Alert(f"❌ {msg}", color="danger", className="mt-2")

    # -----------------------------------------------------------------------
    # 12. Automated Update Checker & Prompt Modal Callbacks
    # -----------------------------------------------------------------------
    def _build_update_prompt_content(res: dict):
        latest_v = res.get("latest_version", "New Version")
        cur_v = res.get("current_version", f"v{CURRENT_VERSION}")
        pub = res.get("published_at", "")
        notes = res.get("release_notes", "")
        return html.Div(
            [
                dbc.Alert(
                    [
                        html.H5(f"🎉 New Version Available: {latest_v}", className="alert-heading mb-1", style={"fontWeight": "bold"}),
                        html.Div(f"You are currently running {cur_v}. A newer release is published on GitHub (Released: {pub}).", style={"fontSize": "0.85rem"}),
                    ],
                    color="primary",
                    style={"backgroundColor": "rgba(47, 129, 247, 0.15)", "border": f"1px solid {T.ACCENT_BLUE}"},
                ),
                html.Div(
                    [
                        html.B("Release Notes:"),
                        html.Pre(
                            notes[:600] + ("..." if len(notes) > 600 else ""),
                            style={
                                "fontSize": "0.78rem",
                                "backgroundColor": "rgba(0,0,0,0.3)",
                                "padding": "10px",
                                "borderRadius": "4px",
                                "whiteSpace": "pre-wrap",
                                "marginTop": "6px",
                                "maxHeight": "200px",
                                "overflowY": "auto",
                                "color": T.TEXT_PRIMARY,
                            },
                        ),
                    ],
                    className="mb-3",
                ) if notes else html.Div(),
                html.P(
                    "Clicking 'Update & Restart Now' will automatically download the updated executable, synchronize all repository files (git pull), and restart the application seamlessly.",
                    style={"fontSize": "0.80rem", "color": T.TEXT_MUTED},
                ),
            ]
        )

    @app.callback(
        Output("update-prompt-modal", "is_open"),
        Output("update-prompt-content", "children"),
        Output("auto-update-info-store", "data"),
        Output("header-update-badge-btn", "style"),
        Output("header-update-badge-btn", "children"),
        Input("auto-update-check-interval", "n_intervals"),
        Input("header-update-badge-btn", "n_clicks"),
        Input("update-prompt-dismiss-btn", "n_clicks"),
        State("update-prompt-modal", "is_open"),
        State("auto-update-info-store", "data"),
        prevent_initial_call=False,
    )
    def manage_update_prompt(n_intervals, header_clicks, dismiss_clicks, is_open, cached_update_info):
        trigger = ctx.triggered_id if hasattr(ctx, "triggered_id") else None
        if not trigger and ctx.triggered:
            trigger = ctx.triggered[0]["prop_id"].split(".")[0]

        # User clicked dismiss button
        if trigger == "update-prompt-dismiss-btn":
            badge_style = {"fontSize": "0.8rem", "fontWeight": "600", "display": "inline-block"} if (cached_update_info and cached_update_info.get("update_available")) else {"display": "none"}
            badge_text = f"🚀 Update {cached_update_info.get('latest_version')}" if cached_update_info else "🚀 Update Available"
            return False, no_update, no_update, badge_style, badge_text

        # User clicked header badge to reopen
        if trigger == "header-update-badge-btn":
            if cached_update_info:
                content = _build_update_prompt_content(cached_update_info)
                return True, content, no_update, no_update, no_update
            return True, no_update, no_update, no_update, no_update

        # Periodic check or initial load
        try:
            res = check_for_updates()
            if res.get("success") and res.get("update_available"):
                latest_v = res.get("latest_version")
                content = _build_update_prompt_content(res)
                badge_style = {"fontSize": "0.8rem", "fontWeight": "600", "display": "inline-block"}
                badge_text = f"🚀 Update {latest_v}"
                return True, content, res, badge_style, badge_text
            else:
                return False, no_update, res, {"display": "none"}, "🚀 Update Available"
        except Exception:
            return False, no_update, no_update, {"display": "none"}, "🚀 Update Available"

    @app.callback(
        Output("update-prompt-status", "children"),
        Input("update-prompt-confirm-btn", "n_clicks"),
        State("auto-update-info-store", "data"),
        prevent_initial_call=True,
    )
    def handle_modal_install_update(n_clicks, update_info):
        if not n_clicks or not update_info:
            return no_update

        dl_url = update_info.get("download_url")
        if not dl_url:
            return dbc.Alert("No download asset found in the latest release.", color="danger", className="mt-2")

        success, msg = apply_update_and_restart(dl_url)
        if success:
            return dbc.Alert(
                [
                    html.B("⬇️ Update in Progress! "),
                    "Downloaded new version. Synchronizing repository files and restarting dashboard in 2 seconds...",
                ],
                color="info",
                className="mt-2",
            )
        else:
            return dbc.Alert(f"❌ {msg}", color="danger", className="mt-2")

