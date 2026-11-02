"""
Tests for UI Enhancements:
1. Light & Dark Theme Support and Header Toggle
2. Multi-Select Dropdowns with Checkboxes and Reset Filters
3. Removal of Header PDF Button
4. Dynamic OS Donut Expansion with CSS Animation
5. Device Roles Extraction and Filtering
"""

import pytest
from src.dashboard import theme as T
from src.dashboard.layout import build_header, build_body
from src.dashboard.components.os_panel import build_os_panel
from src.dashboard.components.org_slicer import build_org_slicer
from src.metrics.data_provider import coordinator
from src.metrics.aggregator import compute_dashboard_slice
from src.api.models import Device, OSInfo, Organization


def test_theme_palette():
    """Verify light and dark palettes return correct background and text colors."""
    dark_p = T.get_theme_palette("dark")
    light_p = T.get_theme_palette("light")

    assert dark_p["is_dark"] is True
    assert dark_p["bg_primary"] == T.BG_PRIMARY
    assert dark_p["text_primary"] == T.TEXT_PRIMARY

    assert light_p["is_dark"] is False
    assert light_p["bg_primary"] == T.LIGHT_BG_PRIMARY
    assert light_p["text_primary"] == T.LIGHT_TEXT_PRIMARY


def test_header_pdf_removed_and_theme_toggle_added():
    """Requirement 1 & 3: Top-right PDF button removed, theme toggle button added."""
    header = build_header(theme_mode="dark")

    def _find_ids(comp):
        ids = []
        if hasattr(comp, "id") and comp.id:
            ids.append(comp.id)
        children = getattr(comp, "children", None)
        if isinstance(children, list):
            for c in children:
                ids.extend(_find_ids(c))
        elif children:
            ids.extend(_find_ids(children))
        return ids

    all_ids = _find_ids(header)
    assert "header-pdf-btn" not in all_ids, "Header PDF button must be removed"
    assert "theme-toggle-btn" in all_ids, "Theme toggle button must be present in header"


def test_multi_select_dropdowns_and_roles_filter():
    """Requirement 2 & 5: Slicer bar replaced with multi-select dropdowns including Device Roles and Reset button."""
    slicer = build_org_slicer(
        org_options=[{"label": "Acme Corp", "value": "1"}],
        location_options=["London Office", "NY HQ"],
        os_family_options=["Windows", "Linux"],
        role_options=["Domain Controller", "Database Server"],
    )

    def _find_component_by_id(comp, target_id):
        if comp is None:
            return None
        if getattr(comp, "id", None) == target_id:
            return comp
        children = getattr(comp, "children", None)
        if isinstance(children, (list, tuple)):
            for c in children:
                res = _find_component_by_id(c, target_id)
                if res is not None:
                    return res
        elif children is not None:
            return _find_component_by_id(children, target_id)
        return None

    # Check dropdowns exist and multi=True
    org_dd = _find_component_by_id(slicer, "filter-org-dropdown")
    loc_dd = _find_component_by_id(slicer, "filter-location-dropdown")
    os_dd = _find_component_by_id(slicer, "filter-os-dropdown")
    roles_dd = _find_component_by_id(slicer, "filter-roles-dropdown")
    reset_btn = _find_component_by_id(slicer, "reset-filters-btn")

    assert org_dd is not None and getattr(org_dd, "multi", False) is True
    assert loc_dd is not None and getattr(loc_dd, "multi", False) is True
    assert os_dd is not None and getattr(os_dd, "multi", False) is True
    assert roles_dd is not None and getattr(roles_dd, "multi", False) is True
    assert reset_btn is not None


def test_os_donut_expansion_only_windows():
    """Requirement 4: When filtered for Windows only, Linux box is omitted and Windows expands with animation."""
    os_data_win_only = {
        "windows_version_counts": {"Windows Server 2022": 10, "Windows Server 2019": 5},
        "linux_version_counts": {},
    }

    panel = build_os_panel(os_data_win_only)
    # Should only have 1 column and it must have lg=12 and os-donut-col-expanded class
    assert len(panel.children) == 1
    col = panel.children[0]
    assert col.lg == 12
    assert "os-donut-col-expanded" in col.className


def test_os_donut_expansion_only_linux():
    """Requirement 4: When filtered for Linux only, Windows box is omitted and Linux expands with animation."""
    os_data_linux_only = {
        "windows_version_counts": {},
        "linux_version_counts": {"Ubuntu 22.04": 8, "RHEL 9": 4},
    }

    panel = build_os_panel(os_data_linux_only)
    assert len(panel.children) == 1
    col = panel.children[0]
    assert col.lg == 12
    assert "os-donut-col-expanded" in col.className


def test_os_donut_both_windows_and_linux():
    """Requirement 4: When both OS families exist, both boxes are rendered side-by-side (lg=6)."""
    os_data_both = {
        "windows_version_counts": {"Windows Server 2022": 10},
        "linux_version_counts": {"Ubuntu 22.04": 8},
    }

    panel = build_os_panel(os_data_both)
    assert len(panel.children) == 2
    assert panel.children[0].lg == 6
    assert panel.children[1].lg == 6


def test_device_roles_filtering():
    """Requirement 5: Test filtering by device role in compute_dashboard_slice."""
    org = Organization(id=1, name="Test Org")
    dev_dc = Device(id=101, display_name="dc-01", organization_id=1, device_role="Domain Controller", os=OSInfo(name="Windows Server 2022"))
    dev_db = Device(id=102, display_name="sql-01", organization_id=1, device_role="Database Server", os=OSInfo(name="Windows Server 2022"))
    dev_app = Device(id=103, display_name="app-01", organization_id=1, device_role="Application Server", os=OSInfo(name="Ubuntu 22.04"))

    all_devs = [dev_dc, dev_db, dev_app]

    # Filter for Domain Controller only
    slice_dc = compute_dashboard_slice(devices=all_devs, organizations=[org], activities=[], active_roles=["Domain Controller"])
    assert slice_dc.total_devices == 1

    # Filter for Domain Controller & Database Server (multi-select)
    slice_multi = compute_dashboard_slice(devices=all_devs, organizations=[org], activities=[], active_roles=["Domain Controller", "Database Server"])
    assert slice_multi.total_devices == 2

    # Filter for Application Server only
    slice_app = compute_dashboard_slice(devices=all_devs, organizations=[org], activities=[], active_roles=["Application Server"])
    assert slice_app.total_devices == 1


def test_filter_bar_single_line_layout():
    """Verify that filter dropdowns and reset button are organized in a compact single dynamic row to save scrolling."""
    slicer = build_org_slicer(
        org_options=[{"label": "Acme Corp", "value": "1"}],
        location_options=["London Office", "NY HQ"],
        os_family_options=["Windows", "Linux"],
        role_options=["Domain Controller", "Database Server"],
    )
    # slicer is a Card whose children is CardBody containing 1 responsive dbc.Row
    card_body = slicer.children
    row = card_body.children
    # Single row contains 6 columns: Org, Country/Location, OS Family, Device Roles, Patch Scope, Reset Button
    assert len(row.children) == 6, "Filter bar must contain all 5 filters + reset button in a single dynamic row"



def test_light_theme_chart_styling():
    """Verify charts apply white background and dark text when theme_mode='light'."""
    from src.dashboard import charts

    # Donut chart
    fig_dark = charts.windows_os_donut({"Windows Server 2022": 5}, theme_mode="dark")
    fig_light = charts.windows_os_donut({"Windows Server 2022": 5}, theme_mode="light")
    assert fig_dark.layout.paper_bgcolor == T.BG_CARD
    assert fig_light.layout.paper_bgcolor == "#FFFFFF"
    assert fig_light.layout.font.color == "#0F172A"

    # Patch gauge
    gauge_light = charts.patch_gauge(88.0, theme_mode="light")
    assert gauge_light.layout.paper_bgcolor == "#FFFFFF"
    assert gauge_light.layout.font.color == "#0F172A"

    # SLA aging bar
    sla_light = charts.patch_sla_aging_bar({"Within SLA (<30d)": 10}, theme_mode="light")
    assert sla_light.layout.paper_bgcolor == "#FFFFFF"
    assert sla_light.layout.font.color == "#0F172A"

    # Hosting donut
    host_light = charts.hosting_donut({"AWS": 5}, theme_mode="light")
    assert host_light.layout.paper_bgcolor == "#FFFFFF"
    assert host_light.layout.font.color == "#0F172A"


def test_panels_theme_mode_support():
    """Verify that all panels accept theme_mode='light' and render cleanly."""
    from src.dashboard.components.kpi_cards import build_kpi_strip
    from src.dashboard.components.map_panel import build_map_panel
    from src.dashboard.components.server_panel import build_server_hosting_panel
    from src.dashboard.components.patch_panel import build_patch_panel
    from src.dashboard.components.eol_panel import build_eol_panel
    from src.dashboard.components.compliance_table import build_compliance_table
    from src.dashboard.components.sla_panel import build_sla_panel
    from src.dashboard.components.reboot_failures_panel import build_reboot_failures_panel
    from src.dashboard.components.reports_panel import build_reports_panel
    from scripts.generate_sample_data import get_mock_dashboard_data

    mock_data = get_mock_dashboard_data()

    # Call each panel with theme_mode="light"
    kpi = build_kpi_strip(mock_data, theme_mode="light")
    assert kpi is not None

    map_p = build_map_panel(mock_data.map_data, theme_mode="light")
    assert map_p is not None

    srv_p = build_server_hosting_panel(mock_data.servers, theme_mode="light")
    assert srv_p is not None

    patch_p = build_patch_panel(mock_data.patches, theme_mode="light")
    assert patch_p is not None

    eol_p = build_eol_panel(mock_data.os, theme_mode="light")
    assert eol_p is not None

    comp_p = build_compliance_table(mock_data.org_table, theme_mode="light")
    assert comp_p is not None

    sla_p = build_sla_panel(mock_data.sla, mock_data.patches, theme_mode="light")
    assert sla_p is not None

    reboot_p = build_reboot_failures_panel(mock_data.sla, theme_mode="light")
    assert reboot_p is not None

    rep_p = build_reports_panel(mock_data, theme_mode="light")
    assert rep_p is not None


def test_settings_modal_theme_support():
    """Verify settings modal builds with theme classes and adapts to light and dark modes."""
    from src.dashboard.components.settings_modal import build_settings_modal

    # Dark mode modal
    dark_modal = build_settings_modal(theme_mode="dark")
    assert "theme-dark" in dark_modal.className
    assert "settings-modal" in dark_modal.className

    # Light mode modal
    light_modal = build_settings_modal(theme_mode="light")
    assert "theme-light" in light_modal.className
    assert "settings-modal" in light_modal.className
    header = light_modal.children[0]
    body = light_modal.children[1]
    footer = light_modal.children[2]

    # Verify light theme backgrounds are applied
    assert header.style["backgroundColor"] == "#FFFFFF"
    assert body.style["backgroundColor"] == "#FFFFFF"
    assert footer.style["backgroundColor"] == "#FFFFFF"


def test_settings_compliance_thresholds_layout_and_no_threshold_input():
    """Verify Discovered Fleet Patch Titles is moved up as the first option, and Allowed Patches input is removed."""
    from src.dashboard.components.settings_modal import build_settings_modal

    modal = build_settings_modal()

    def _collect_ids_in_order(comp):
        ids = []
        if hasattr(comp, "id") and comp.id:
            ids.append(comp.id)
        children = getattr(comp, "children", None)
        if isinstance(children, (list, tuple)):
            for c in children:
                ids.extend(_collect_ids_in_order(c))
        elif children is not None:
            ids.extend(_collect_ids_in_order(children))
        return ids

    all_ids = _collect_ids_in_order(modal)

    # 1. Allowed patches threshold input must be completely removed
    assert "settings-server-patch-threshold" not in all_ids, "settings-server-patch-threshold must be removed"

    # 2. Discovered fleet patch titles must exist and appear before target patch keywords
    assert "settings-discovered-patch-titles" in all_ids
    assert "settings-patch-included-keywords" in all_ids
    idx_discovered = all_ids.index("settings-discovered-patch-titles")
    idx_keywords = all_ids.index("settings-patch-included-keywords")
    assert idx_discovered < idx_keywords, "Discovered Fleet Patch Titles must appear as the first option before patch keywords"


def test_country_and_org_name_slicer_filtering():
    """Verify that filtering by Country, Country Name, Org Name, and Org ID recalculates live slice correctly."""
    from scripts.generate_sample_data import _generate_raw_mock
    from src.metrics.aggregator import compute_dashboard_slice

    orgs, devices, activities = _generate_raw_mock()
    assert len(devices) > 0

    # 1. Test filtering by Country code (USA)
    slice_usa = compute_dashboard_slice(devices, orgs, activities, active_location=["USA"])
    assert slice_usa.total_devices > 0
    assert all((d.country == "USA" or "usa" in (d.location_name or "").lower() or "usa" in (d.region or "").lower()) for d in slice_usa.devices_filtered)

    # 2. Test filtering by Friendly Country Name (Germany)
    slice_germany = compute_dashboard_slice(devices, orgs, activities, active_location=["Germany"])
    assert slice_germany.total_devices > 0
    assert all((d.country == "DEU" or "germany" in (d.location_name or "").lower() or "europe" in (d.region or "").lower()) for d in slice_germany.devices_filtered)

    # 3. Test filtering by Organization Name string without crashing int()
    sample_org = orgs[0]
    slice_org_name = compute_dashboard_slice(devices, orgs, activities, active_org_id=[sample_org.name])
    assert slice_org_name.total_devices > 0
    assert all(d.organization_id == sample_org.id for d in slice_org_name.devices_filtered)

    # 4. Test Slicer Bar Country / Location placeholder and single-row layout
    slicer = build_org_slicer(
        org_options=[{"label": sample_org.name, "value": str(sample_org.id)}],
        location_options=["USA", "DEU", "London Office"],
        os_family_options=["Windows", "Linux"],
        role_options=["Domain Controller"],
    )
    # Check that country options are formatted with flags and friendly names
    def _find_component_by_id(comp, target_id):
        if comp is None:
            return None
        if getattr(comp, "id", None) == target_id:
            return comp
        children = getattr(comp, "children", None)
        if isinstance(children, (list, tuple)):
            for c in children:
                res = _find_component_by_id(c, target_id)
                if res is not None:
                    return res
        elif children is not None:
            return _find_component_by_id(children, target_id)
        return None

    loc_dd = _find_component_by_id(slicer, "filter-location-dropdown")
    assert loc_dd is not None
    assert loc_dd.placeholder == "All Countries / Locations..."
    loc_vals = [opt["value"] for opt in loc_dd.options]
    assert "USA" in loc_vals and "DEU" in loc_vals


def test_actual_filter_names_in_active_filter_label_and_reports():
    """Verify that multiple selected organizations, locations, and roles show actual names, not '2 Orgs'."""
    from scripts.generate_sample_data import _generate_raw_mock
    from src.metrics.aggregator import compute_dashboard_slice
    from src.reporting.html_export import generate_html_report
    from src.metrics.pdf_export import generate_pdf_report

    orgs, devices, activities = _generate_raw_mock()
    assert len(orgs) >= 2

    # Multiple orgs selected by ID
    selected_org_ids = [orgs[0].id, orgs[1].id]
    slice_data = compute_dashboard_slice(
        devices,
        orgs,
        activities,
        active_org_id=selected_org_ids,
        active_location=["USA", "DEU"],
        active_roles=["Domain Controller", "Web Server"],
    )

    # Label MUST contain actual organization names, location names, and role names
    label = slice_data.active_filter_label
    assert "2 Orgs" not in label
    assert "2 Locs" not in label
    assert "2 Roles" not in label
    assert orgs[0].name in label
    assert orgs[1].name in label
    assert "USA" in label
    assert "DEU" in label
    assert "Domain Controller" in label
    assert "Web Server" in label

    # Verify that exported HTML contains actual organization names in scope badge
    html_out = generate_html_report(slice_data)
    assert orgs[0].name in html_out
    assert orgs[1].name in html_out
    assert "2 Orgs" not in html_out

    # Verify that exported PDF contains actual organization names in scope
    pdf_out = generate_pdf_report(slice_data)
    assert isinstance(pdf_out, bytes)
    assert len(pdf_out) > 1000


def test_patch_operations_details_tab_and_tables():
    """Verify that Patch Operations Details renders the 2 new tables with exact requested columns."""
    from src.dashboard.components.sla_panel import build_sla_panel, _TOP_SERVERS_COLUMNS, _TOP_PATCHES_COLUMNS
    from scripts.generate_sample_data import get_mock_dashboard_data

    mock_data = get_mock_dashboard_data()
    panel = build_sla_panel(mock_data.sla, mock_data.patches, theme_mode="light")
    panel_str = str(panel)

    # Check table IDs
    assert "top-servers-pending-table" in panel_str
    assert "top-patches-pending-table" in panel_str

    # Check Table 1 column headers
    server_col_names = [col["name"] for col in _TOP_SERVERS_COLUMNS]
    assert server_col_names == ["Server Name", "Org", "Loc", "OS name", "Device Role", "Approve patch Count"]

    # Check Table 2 column headers
    patch_col_names = [col["name"] for col in _TOP_PATCHES_COLUMNS]
    assert patch_col_names == [
        "Patch Name",
        "Patch Type (Critical / Important)",
        "OS/Software type patch",
        "Pending device count",
        "Patch release date",
    ]


def test_patch_panel_donut_chart_inclusion():
    """Verify that OS vs 3rd-Party Software Breakdown donut chart is in build_patch_panel."""
    from src.dashboard.components.patch_panel import build_patch_panel
    from scripts.generate_sample_data import get_mock_dashboard_data

    mock_data = get_mock_dashboard_data()
    panel = build_patch_panel(mock_data.patches, theme_mode="light", sla_data=mock_data.sla)
    panel_str = str(panel)

    assert "patch-type-donut" in panel_str
    assert "fleet-patch-coverage-gauge" in panel_str
    assert "patch-compliance-ytd-line" in panel_str


def test_navigation_renamed_patch_operations_details():
    """Verify navigation tab is renamed to 'Patch Operations Details'."""
    from src.dashboard.layout import build_body
    from scripts.generate_sample_data import get_mock_dashboard_data

    mock_data = get_mock_dashboard_data()
    body = build_body(mock_data)
    body_str = str(body)

    assert "Patch Operations Details" in body_str
    assert "Patch Operations & SLA Aging" not in body_str


def test_settings_modal_5_columns_eol_layout():
    """Verify Section 5 in Settings Modal uses 5-column layout for compact display."""
    from src.dashboard.components.settings_modal import build_settings_modal

    modal = build_settings_modal(theme_mode="light")
    modal_str = str(modal)

    assert "0 0 20%" in modal_str





