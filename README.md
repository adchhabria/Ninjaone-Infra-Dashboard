# NinjaOne Infra Dashboard & Unified Patch Toolkit ⚡

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Dash](https://img.shields.io/badge/Dash-2.16+-00D8FF.svg)](https://dash.plotly.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Release](https://img.shields.io/badge/Release-v1.0.20-brightgreen.svg)](https://github.com/adchhabria/Ninjaone-Infra-Dashboard/releases)
[![Tests](https://img.shields.io/badge/tests-84%20passed-success.svg)](tests/)

An enterprise-grade infrastructure intelligence and operational patch management toolkit designed for **NinjaOne RMM**. Built for MSPs, IT infrastructure leaders, and compliance auditors to monitor multi-tenant device health, SLA aging backlogs, OS compliance thresholds, and multi-cloud hosting environments in real time.

---

## 📐 Architecture & Telemetry Pipeline

![NinjaOne Toolkit Architecture](./ninjaone-management-dashboard-toolkit.svg)

<p align="center">
  <b><a href="./ninjaone-architecture-showcase.html">🌐 Open Interactive Architecture Showcase (`HTML`)</a></b>
</p>

---

## ⚡ Key Advantages & Operational Capabilities

* **⏱️ Zero Setup & Instant Portability**: Available as a single standalone executable (`Ninjaone-Infra-Dashboard.exe`). No Python runtime, browser drivers, or environment setup required.
* **🛑 Automatic Browser-Close Process Shutdown**: An intelligent client-to-server heartbeat and background watchdog daemon monitor active dashboard sessions. When the browser tab or window is closed, the executable terminates cleanly, freeing system memory and releasing port `8050` so future launches start with zero port conflicts.
* **🎯 Selective Patch & KB Compliance Governance**:
  * **Strict Targeted Compliance**: Administrators can choose specific discovered patch titles or Knowledge Base identifiers (e.g., `KB5127648` or `2024-10 Cumulative Update for Windows Server 2022`) in *Settings > Compliance & Thresholds*.
  * **Precision Evaluation**: A server is marked **Non-Compliant** *only if* it is missing any of the selected patches. Servers with the selected patches installed (or not pending) evaluate as **Compliant**, preventing unrelated 3rd-party software updates or unselected patches from distorting compliance metrics.
  * **Fleet Fallback**: When no individual patches are selected, the engine defaults to evaluating fleet-wide OS Cumulative and Security Updates while filtering out noisy product updates (.NET, Office, SQL Server, etc.).
* **🌗 Full-Spectrum Dark & Light Theme System**:
  * **Light Mode**: Clean enterprise palette featuring high-contrast dark slate typography (`#0F172A`) on soft light backgrounds (`#F8FAFC`).
  * **Dark Mode**: High-legibility, glare-free dark slate theme with softened filter text (`#94A3B8` / `#CBD5E1`) and muted placeholders (`#64748B`) to prevent eye fatigue.
  * **Complete Theme Consistency**: Persisted via browser local storage and applied across all 4 operational workspaces, settings modals, and exported audit reports.
* **🎛️ Dynamic Single-Row Ergonomic Filter Bar**:
  * Multi-dimensional filtering across **Organization**, **Country / Location**, **OS Family**, **Device Role**, and **Patch Scope**.
  * Sizing dynamically adjusts to fit in a single streamlined row without awkward line wraps, with right-aligned dropdown arrows and non-overlapping text layout.
  * Live filter badge counters and a 1-click **↺ Reset Filters** button.
* **📄 Theme-Aware & Contextual Audit Exports**:
  * **Multi-Format Export**: Generates self-contained interactive HTML reports, multi-page vector PDFs, and 6-sheet formatted Excel workbooks.
  * **Theme Matching**: Exported HTML and PDF reports automatically adopt the active dashboard theme (Light or Dark), complete with enlarged KPI summary numbers.
  * **Descriptive Scope Badges**: Displays full entity names (e.g., `"Orgs: Headquarters - New York, London EMEA Hub"`) instead of ambiguous count summaries.
* **✨ Animated OS Donut Expansion**: Smart CSS expansion (`.os-donut-col-expanded`) automatically hides empty operating system cards and smoothly scales Windows or Linux donuts to full width when filtered.
* **🛡️ Device Roles Intelligence**: Automated extraction and categorization of server roles (Domain Controller, Database Server, Web Server, File Server, Application Server, Backup Server, Workstation) enabling role-targeted compliance filtering.
* **⚡ Sub-Millisecond Zero-Latency Performance**: In-memory slice caching delivers sub-millisecond (**0.02 ms**) filter responses; network circuit-breaking stops background retry freezes; and granular Dash callbacks update only target DOM nodes without re-mounting canvas elements.
* **📊 4 Specialized Operational Workspaces**:
  * **Executive Overview**: High-level fleet KPIs, interactive WebGL/SVG world map, OS distribution, hosting split, and compliance gauges.
  * **Patch Operations & SLA Aging**: Granular SLA aging backlogs (<30d, 31-60d, 61-90d, 90d+) and severity breakdowns.
  * **Reboots & Failure Watchlist**: Real-time tracking of pending reboot states and recurring patch failures.
  * **Reports & Excel Export**: Filter-aware downloads in Interactive HTML, multi-page vector PDF, and 6-sheet formatted Excel workbooks.
* **🔄 Built-In Auto-Updater**: In-app version checks, background downloads with progress feedback, and seamless zero-lock binary restarts.

---

## 📂 Project Structure

```
ninjaone-dashboard/
├── .github/
│   └── workflows/
│       └── build_release.yml          # GitHub Actions automated release pipeline
├── scripts/
│   ├── build_single_exe.py            # Standalone single .exe PyInstaller packager
│   ├── build_exe.py                   # Directory-based distribution packager
│   ├── export_pdf.py                  # Standalone vector PDF generation utility
│   ├── generate_sample_data.py        # Mock dataset generator & sub-ms RAM slice cache
│   └── version_info.txt               # Windows PE executable version metadata
├── src/
│   ├── api/
│   │   ├── actions.py                 # Device actions (reboots, scans, maintenance)
│   │   ├── activities.py              # NinjaOne activity feed & audit query client
│   │   ├── alerts.py                  # Fleet active alerts ingestion
│   │   ├── client.py                  # NinjaOne REST API client with OAuth2 PKCE
│   │   ├── devices.py                 # Fleet device queries & hardware metadata
│   │   ├── models.py                  # Pydantic data models & device role classifier
│   │   ├── organizations.py           # Multi-tenant organization & location queries
│   │   ├── patches.py                 # Patch catalog queries & approval models
│   │   └── pkce_auth.py               # RFC 7636 OAuth 2.0 PKCE authentication flow
│   ├── cache/
│   │   └── ttl_cache.py               # Local disk & memory TTL caching layer
│   ├── dashboard/
│   │   ├── assets/
│   │   │   └── custom.css             # Theme variables, badges & expansion animations
│   │   ├── components/
│   │   │   ├── alerts_panel.py        # Active alert summaries & severity matrix
│   │   │   ├── compliance_table.py    # Non-compliant servers & patch inventory table
│   │   │   ├── eol_panel.py           # End-of-life OS breakdown charts
│   │   │   ├── kpi_cards.py           # Executive metric cards
│   │   │   ├── map_panel.py           # Interactive world map datacenter visualization
│   │   │   ├── org_slicer.py          # Dynamic single-row multi-select filter bar
│   │   │   ├── os_panel.py            # Windows & Linux OS donut charts (animated)
│   │   │   ├── patch_panel.py         # Patch status overview & compliance gauge
│   │   │   ├── reboot_failures_panel.py # Reboot status & failure watchlist
│   │   │   ├── reports_panel.py       # Report export controls & format selector
│   │   │   ├── server_panel.py        # Server hosting & infrastructure panels
│   │   │   ├── settings_modal.py      # Governance, thresholds & PKCE auth modal
│   │   │   └── sla_panel.py           # Patch aging & SLA compliance charts
│   │   ├── app.py                     # Dash application entry point & watchdog monitor
│   │   ├── callbacks.py               # Granular event routing & fast tab switcher
│   │   ├── charts.py                  # Themed Plotly visualization builders
│   │   ├── layout.py                  # Root application layout & nav shell
│   │   └── theme.py                   # Dark & Light palette constants & helpers
│   ├── metrics/
│   │   ├── aggregator.py              # Multi-tenant metrics slice aggregator
│   │   ├── alert_summary.py           # Alert metric rollup & device mapping
│   │   ├── data_provider.py           # Unified coordinator & network circuit breaker
│   │   ├── excel_export.py            # OpenPyXL 6-sheet audit report generator
│   │   ├── os_compliance.py           # OS lifecycle & End-of-Life calculation
│   │   ├── patch_compliance.py        # Selective & fleet update compliance evaluator
│   │   ├── patch_sla.py               # SLA aging backlog & bucket analysis
│   │   ├── pdf_export.py              # ReportLab multi-page vector PDF generator
│   │   └── server_hosting.py          # Multi-cloud & hypervisor classification
│   ├── reporting/
│   │   └── html_export.py             # Self-contained theme-aware HTML report exporter
│   └── utils/
│       ├── ssl_helper.py              # Enterprise TLS & SSL cert helper
│       └── updater.py                 # Semantic version checker & auto-updater
├── tests/
│   ├── test_charts.py                 # Visualization rendering tests
│   ├── test_client.py                 # API authentication & client tests
│   ├── test_download_callbacks.py     # Filtered export endpoint & theme tests
│   ├── test_excel_export.py           # Excel workbook integrity tests
│   ├── test_html_export.py            # Standalone HTML export & theme tests
│   ├── test_metrics.py                # Aggregation & OS compliance rules tests
│   ├── test_patch_sla.py              # Patch aging backlog calculation tests
│   ├── test_patches_api.py            # Patch API & exclusion parsing tests
│   ├── test_pdf_export.py             # Vector PDF rendering & theme tests
│   ├── test_pkce_auth.py              # PKCE authorization flow tests
│   ├── test_selective_compliance_and_heartbeat.py # Selective compliance & watchdog tests
│   ├── test_ui_enhancements.py        # Themes, multi-select, role & animation tests
│   └── test_updater.py                # Update checking & semver tests
├── config.yaml                        # Global SLA & compliance defaults
├── launcher.py                        # Desktop launcher with auto-browser & watchdog
├── Ninjaone-Infra-Dashboard.exe       # Pre-compiled standalone Windows binary
├── requirements.txt                   # Production dependencies
└── version.json                       # Version manifest (v1.0.20)
```

---

## 🚀 Quick Start

### Option 1: Standalone Binary (Windows)
Download the latest `Ninjaone-Infra-Dashboard.exe` from [Releases](https://github.com/adchhabria/Ninjaone-Infra-Dashboard/releases) and double-click to launch.
* Automatically launches the default web browser to the dashboard.
* Automatically terminates background server tasks when the browser window is closed.
* Requires zero Python installation, drivers, or system configuration.

### Option 2: Run from Source
```bash
git clone https://github.com/adchhabria/Ninjaone-Infra-Dashboard.git
cd Ninjaone-Infra-Dashboard
python -m venv venv && .\venv\Scripts\activate
pip install -r requirements.txt

# Run in Interactive Demo Mode (No API keys required)
python src/dashboard/app.py --demo
```
Access the dashboard at **[http://localhost:8050](http://localhost:8050)**.

---

## ⚙️ NinjaOne Connection

Configure your API credentials in **⚙️ Settings** within the web UI, or set environment variables in `.env`:

```ini
NINJA_BASE_URL=https://app.ninjarmm.com  # or https://eu.ninjarmm.com, https://oc.ninjarmm.com
NINJA_CLIENT_ID=your_client_id
NINJA_CLIENT_SECRET=your_client_secret
```

Alternatively, use the **🔐 Sign In to NinjaOne** button in the header or Settings modal to authenticate securely via interactive **OAuth 2.0 PKCE** with browser redirection.

*Required API Scopes: `monitoring`, `management`, `control` (optional for remote reboot/rescan triggers).*

---

## 🛠️ Build & Test

```bash
# Run complete test suite (83 automated tests)
python -m pytest

# Compile single standalone Windows executable
python scripts/build_single_exe.py
```

---

## 📄 License

Distributed under the [MIT License](LICENSE).
