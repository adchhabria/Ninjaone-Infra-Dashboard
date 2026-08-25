"""
NinjaOne Dashboard — Application Entry Point.

Usage:
    # Default (automatically connects to live NinjaOne if credentials configured, or runs in Demo Mode):
    python src/dashboard/app.py

    # Explicit Demo mode:
    python src/dashboard/app.py --demo

    # Custom port:
    python src/dashboard/app.py --port 8050
"""

from __future__ import annotations

import argparse
import os
import sys

import dash
import dash_bootstrap_components as dbc
from rich.console import Console

# Ensure project root is on sys.path when running directly or frozen
if getattr(sys, "frozen", False):
    _root_dir = sys._MEIPASS
else:
    _root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)

from src.dashboard import theme as T
from src.dashboard.callbacks import register_callbacks
from src.dashboard.layout import build_layout
from src.metrics.data_provider import coordinator

console = Console()


# ---------------------------------------------------------------------------
# App Factory
# ---------------------------------------------------------------------------

def create_app(get_data_fn=None) -> dash.Dash:
    """
    Create and configure the Dash application.
    """
    if get_data_fn is None:
        get_data_fn = coordinator.get_dashboard_data

    app = dash.Dash(
        __name__,
        external_stylesheets=[
            dbc.themes.DARKLY,
            "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap",
        ],
        title="Ninjaone Infra Dashboard",
        suppress_callback_exceptions=True,
        meta_tags=[
            {"name": "viewport", "content": "width=device-width, initial-scale=1"},
        ],
    )

    def serve_layout():
        data = get_data_fn(
            active_org_id=None,
            active_region="Global / All",
            active_location="All Locations",
            active_os_family="All OS Families",
        )
        return build_layout(data)

    app.layout = serve_layout
    register_callbacks(app, get_data_fn)
    return app


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="NinjaOne IT Compliance Dashboard")
    parser.add_argument("--demo", action="store_true", help="Force demo mode with sample dataset")
    parser.add_argument("--port", type=int, default=int(os.getenv("DASH_PORT", 8050)))
    parser.add_argument("--debug", action="store_true",
                        default=os.getenv("DASH_DEBUG", "false").lower() == "true")
    args = parser.parse_args()

    console.print("\n[bold cyan]NinjaOne IT Compliance & Infrastructure Dashboard[/bold cyan]")
    console.print("=" * 60)

    if args.demo:
        os.environ["DEMO_MODE"] = "true"
        console.print("[yellow]>> Demo Mode Active -- Full interactive mock infrastructure dataset[/yellow]")
    else:
        if coordinator.is_live:
            console.print(f"[green]>> Live Mode Active -- Connected to NinjaOne API ({coordinator.base_url})[/green]")
        else:
            console.print("[yellow]>> Starting in Demo Mode (Connect anytime via Sign In button)[/yellow]")

    app = create_app(coordinator.get_dashboard_data)

    console.print(f"\n[bold green]Dashboard live at:[/bold green] http://localhost:{args.port}")
    console.print("[dim]Press Ctrl+C to exit.[/dim]\n")

    app.run(debug=args.debug, port=args.port, host="0.0.0.0")


if __name__ == "__main__":
    main()
