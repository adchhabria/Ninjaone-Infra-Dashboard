"""
NinjaOne Dashboard — Application Entry Point.

Usage:
    # Live mode (connects to NinjaOne via API):
    python src/dashboard/app.py

    # Demo mode (uses mock data with full slicer & map interactivity):
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

# Ensure project root is on sys.path when running directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from src.dashboard import theme as T
from src.dashboard.callbacks import register_callbacks
from src.dashboard.layout import build_layout

console = Console()


# ---------------------------------------------------------------------------
# App Factory
# ---------------------------------------------------------------------------

def create_app(get_data_fn) -> dash.Dash:
    """
    Create and configure the Dash application.

    Args:
        get_data_fn: Callable(active_org_id, active_region, active_location, active_os_family) -> DashboardData
    """
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
    parser.add_argument("--demo", action="store_true", help="Run in demo mode with sample dataset")
    parser.add_argument("--port", type=int, default=int(os.getenv("DASH_PORT", 8050)))
    parser.add_argument("--debug", action="store_true",
                        default=os.getenv("DASH_DEBUG", "false").lower() == "true")
    args = parser.parse_args()

    console.print("\n[bold cyan]NinjaOne IT Compliance & Infrastructure Dashboard[/bold cyan]")
    console.print("=" * 60)

    if args.demo or os.getenv("DEMO_MODE", "false").lower() == "true":
        console.print("[yellow]>> Demo Mode Active -- Full interactive mock infrastructure dataset[/yellow]")
        from scripts.generate_sample_data import get_mock_dashboard_data
        get_data_fn = get_mock_dashboard_data
    else:
        console.print("[green]>> Live Mode Active -- Authenticating with NinjaOne Public API[/green]")
        from dotenv import load_dotenv
        load_dotenv()

        from src.api.client import NinjaOneClient
        from src.metrics.aggregator import MetricsAggregator

        cache_ttl = int(os.getenv("CACHE_TTL_SECONDS", 300))
        client = NinjaOneClient.from_env()
        aggregator = MetricsAggregator(client, cache_ttl=cache_ttl)
        get_data_fn = aggregator.get_dashboard_data

    app = create_app(get_data_fn)

    console.print(f"\n[bold green]Dashboard live at:[/bold green] http://localhost:{args.port}")
    console.print("[dim]Press Ctrl+C to exit.[/dim]\n")

    app.run(debug=args.debug, port=args.port, host="0.0.0.0")


if __name__ == "__main__":
    main()
