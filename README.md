# Ninjaone Infra Dashboard & Unified Patch Toolkit ⚡

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Dash](https://img.shields.io/badge/Dash-2.16+-00D8FF.svg)](https://dash.plotly.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)]()

An enterprise-grade, C-level infrastructure intelligence and operational patch management toolkit designed specifically for **NinjaOne RMM**. Built for MSPs, enterprise IT infrastructure architects, and compliance officers to monitor multi-tenant device health, SLA aging backlogs, and multi-cloud hosting environments in real time.

---

## 🌟 Key Features

### 1. 📊 Executive Overview & Infrastructure Map
- **Executive KPI Strip**: Total Managed Devices, Online %, Overall Compliance Score (RAG color-coded), Server Fleet, and EOL Devices at Risk.
- **Triple Excel-Style Slicer Bar**: 1-click stacked filter pills for:
  - 🏢 **Organizations / Clients**
  - 📍 **Locations / Branch Sites**
  - 💻 **OS Families** (*Windows*, *Linux*, *macOS*)
- **Geographic Infrastructure & Compliance Map**: Dark-themed interactive world map with circle bubble diameters dynamically scaled to each country's device volume, featuring hover-only tooltip inspection.
- **Operating System Landscape**: Two dedicated side-by-side donut charts for **Windows OS Builds** and **Linux Distributions**.
- **Server Compliance & Roles**: Dedicated server fleet breakdown (*Domain Controllers*, *File*, *Database*, *Web*, *Application*, and *Backup Servers*).
- **Server Hosting Infrastructure**: Multi-cloud and virtualization breakdown across **AWS**, **Azure**, **GCP**, **Virtual Machines (VMs / VMware / Hyper-V)**, and **Physical Hardware**.
- **Patch Management Speedometer Gauge**: Color-coded coverage gauge with exact enterprise SLA thresholds (🔴 `0-60%` Red, 🟡 `61-84%` Amber, 🟢 `85%+` Green).
- **Dedicated EOL Lifecycle Ledger**: Complete audit table of obsolete OS builds with days overdue, EOL dates, and risk scores (`CRITICAL`, `HIGH`, `MEDIUM`).
- **Organization Compliance Table**: Multi-tenant client ledger with RAG status and multi-column sorting.

### 2. ⏱️ Patch Operations & SLA Aging Hub *(Inspired by patch-toolkit)*
- **Patch SLA Aging Backlog**: Bar chart tracking overdue patches across 4 brackets:
  - 🟢 `< 7 Days` (Within SLA)
  - 🟡 `8 - 30 Days` (Warning)
  - 🟠 `31 - 90 Days` (High Risk)
  - 🔴 `> 90 Days` (Critical SLA Breach)
- **OS vs 3rd-Party Software Breakdown**: Donut chart tracking Microsoft KBs vs Chrome, Zoom, Adobe, and runtimes.
- **Fleet Patch Inventory DataTable**: Searchable, sortable ledger with Excel-style column filters.

### 3. 🔄 Reboots & Failure Watchlist
- **Pending Reboot Ledger**: Endpoints requiring restart to finalize patch installations, with uptime in days and pending patch counts.
- **Patch Deployment Failure Triage**: Endpoints with failed updates, error codes (e.g. `0x80070002`, `0x80240020`), and attempt counters.
- **Remediation Action Triggers**: Remote "Bulk Reboot" and "Fleet Patch Rescan" API triggers.

### 4. 📥 Reports & Enterprise Excel Export
- **Multi-Sheet Excel Workbook (`.xlsx`)**: One-click download with 6 formatted worksheets:
  1. `Executive Summary`
  2. `Organization Compliance`
  3. `EOL Device Ledger`
  4. `Patch SLA Aging`
  5. `Needs Reboot`
  6. `Patch Failures`
- **Executive PDF Presentation**: Pixel-perfect headless reporting engine.

### 5. 🔍 Excel-Style Table Filtering & Multi-Column Sorting
- Every table features an interactive **`🔍 Filter...`** row beneath each column header supporting instantaneous text search and comparison queries (`> 30`, `< 60`, `>= 85`).
- Click any header to sort ascending (`▲`) or descending (`▼`) across multiple columns simultaneously.

---

## 🚀 Quick Start (Running Locally)

### Option A: Clone & Run with Python (Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/adchhabria/ninjaone-infra-dashboard.git
cd ninjaone-infra-dashboard

# 2. Create and activate a virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Launch in Interactive Demo Mode (No API keys required to test)
python src/dashboard/app.py --demo

# Or launch the Desktop Browser Launcher:
python launcher.py
```
Open **[http://localhost:8050](http://localhost:8050)** in your browser.

---

## ⚙️ Connecting to Your Live NinjaOne Tenant

You can connect the dashboard to your live NinjaOne tenant in **under 2 minutes**:

### Step 1: Create an API Client in NinjaOne
1. In your NinjaOne console, navigate to **Administration > Apps > API**.
2. Click **Add API Client**.
3. Set the application type to **Machine-to-Machine (Client Credentials)**.
4. Select the following scopes:
   - `monitoring` (Read devices, organizations, alerts)
   - `management` (Read patch status, software inventory)
   - `control` (Optional: for reboot & patch scan triggers)
5. Save and copy your **Client ID** and **Client Secret**.

### Step 2: Configure Credentials in the Dashboard
- **Method 1 (In-App GUI)**: Open the dashboard, click **⚙️ Settings** in the top-right header, enter your Base URL, Client ID, and Client Secret, and click **Save Settings**.
- **Method 2 (`.env` file)**: Copy `.env.example` to `.env` and fill in your details:

```ini
NINJA_BASE_URL=https://app.ninjarmm.com
# For EU region: https://eu.ninjarmm.com
# For Oceania:   https://oc.ninjarmm.com

NINJA_CLIENT_ID=your_client_id_here
NINJA_CLIENT_SECRET=your_client_secret_here

CACHE_TTL_SECONDS=300
DASH_PORT=8050
```

### Step 3: Run in Live Mode
```bash
python src/dashboard/app.py
```
The dashboard will authenticate, pull your organizations, locations, and endpoints based on your user's role-based access control (RBAC), and build your live compliance view.

---

## 📦 Building a Standalone Windows Executable (.exe)

You can bundle this entire toolkit into a single, self-contained Windows desktop app:

```bash
# Build the standalone package
python scripts/build_exe.py
```
The compiled application will be generated in `dist/NinjaOne-Compliance-Dashboard/`. Anyone can double-click `NinjaOne-Dashboard.exe` without needing Python installed!

---

## 🧪 Running Unit Tests

The test suite includes 26 automated unit tests covering API clients, EOL lifecycle detection, multi-cloud hosting classification, and Excel generation:

```bash
python -m pytest tests/ -v
```

---

## 📁 Repository Structure

```
ninjaone-infra-dashboard/
├── .github/workflows/          # Automated GitHub Actions release pipeline
├── scripts/
│   ├── build_exe.py            # PyInstaller desktop bundling script
│   ├── export_pdf.py           # Headless PDF report generator
│   └── generate_sample_data.py # Mock multi-tenant data generator
├── src/
│   ├── api/                    # NinjaOne REST API client & models
│   ├── cache/                  # In-memory TTL caching engine
│   ├── dashboard/              # Dash web application, charts & components
│   │   ├── components/         # Slicers, Map, OS Donuts, Server, Patch, EOL, SLA
│   │   ├── charts.py           # Plotly dark theme chart builders
│   │   ├── layout.py           # 4-Tab navigation layout
│   │   └── callbacks.py        # Interactive slicing & download callbacks
│   └── metrics/                # SLA aging, EOL detection, hosting classification
├── tests/                      # Pytest automated test suite
├── launcher.py                 # Desktop auto-browser launcher
├── requirements.txt            # Python dependencies
└── README.md                   # Documentation
```

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.
