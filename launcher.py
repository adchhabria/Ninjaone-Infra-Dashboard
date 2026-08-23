"""
Desktop Launcher for Standalone NinjaOne Dashboard Executable.

Starts the local Dash server in a worker thread and immediately opens
the user's default web browser to the dashboard URL.
"""

from __future__ import annotations

import os
import sys
import threading
import time
import webbrowser

# Ensure bundle directory is in path
if getattr(sys, "frozen", False):
    bundle_dir = sys._MEIPASS  # type: ignore
else:
    bundle_dir = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, bundle_dir)

from src.dashboard.app import create_app


def launch_browser(url: str = "http://localhost:8050"):
    """Wait briefly for server spin-up and open the default browser."""
    time.sleep(1.8)
    webbrowser.open(url)


def main():
    print("=" * 60)
    print("⚡ NinjaOne IT Compliance & Infrastructure Dashboard")
    print("=" * 60)
    print("Starting local dashboard engine...")

    # Load environment or fallback to demo mode if credentials are unset
    from dotenv import load_dotenv
    load_dotenv()

    client_id = os.getenv("NINJA_CLIENT_ID")
    client_secret = os.getenv("NINJA_CLIENT_SECRET")

    if client_id and client_secret:
        print("[+] Connecting to live NinjaOne API...")
        from src.api.client import NinjaOneClient
        from src.metrics.aggregator import MetricsAggregator
        client = NinjaOneClient.from_env()
        aggregator = MetricsAggregator(client)
        get_data_fn = aggregator.get_dashboard_data
    else:
        print("[!] No credentials found in .env — starting in Demo Mode.")
        print("[!] You can configure your API credentials anytime in the Settings menu in the top right.")
        from scripts.generate_sample_data import get_mock_dashboard_data
        get_data_fn = get_mock_dashboard_data

    app = create_app(get_data_fn)

    # Launch browser in separate thread
    threading.Thread(target=launch_browser, daemon=True).start()

    print("\nDashboard available at: http://localhost:8050")
    print("Opening in your default browser...\n")
    print("To stop the dashboard, close this window or press Ctrl+C.\n")

    app.run(debug=False, port=8050, host="127.0.0.1")


if __name__ == "__main__":
    main()
