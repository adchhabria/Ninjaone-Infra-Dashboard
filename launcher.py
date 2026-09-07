"""
Desktop Launcher for Standalone NinjaOne Dashboard Executable.

Starts the local Dash server silently in the background and opens
the user's default web browser to the dashboard URL.
"""

from __future__ import annotations

import os
import sys
import threading
import time
import webbrowser

# Safely handle stdout/stderr in windowless (--noconsole) mode on Windows
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")


def hide_console():
    """Hides the console window immediately upon startup in Windows."""
    try:
        import ctypes
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 0)  # 0 = SW_HIDE
    except Exception:
        pass


hide_console()

# Ensure bundle directory is in path
if getattr(sys, "frozen", False):
    bundle_dir = sys._MEIPASS  # type: ignore
else:
    bundle_dir = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, bundle_dir)

from src.dashboard.app import create_app
from src.metrics.data_provider import coordinator


def launch_browser(url: str = "http://localhost:8050"):
    """Wait briefly for server spin-up and open the default browser."""
    time.sleep(1.5)
    try:
        webbrowser.open(url)
    except Exception:
        pass


def main():
    hide_console()

    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()

    # Use unified coordinator for live PKCE/client-credentials & demo dataset
    app = create_app(coordinator.get_dashboard_data)

    # Launch browser in separate background thread
    threading.Thread(target=launch_browser, daemon=True).start()

    # Run the server silently
    app.run(debug=False, port=8050, host="127.0.0.1")


if __name__ == "__main__":
    main()
