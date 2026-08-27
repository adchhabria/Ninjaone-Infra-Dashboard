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
from flask import render_template_string, request
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

    # -----------------------------------------------------------------------
    # OAuth 2.0 PKCE Callback Endpoint
    # -----------------------------------------------------------------------
    @app.server.route("/oauth/callback")
    def oauth_callback():
        code = request.args.get("code")
        state = request.args.get("state")
        error = request.args.get("error")
        error_description = request.args.get("error_description", "")

        if error:
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>NinjaOne Login Failed</title>
                <style>
                    body {{ font-family: 'Segoe UI', sans-serif; background: #0D1117; color: #E6EDF3; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }}
                    .card {{ background: #161B22; border: 1px solid #F44336; border-radius: 10px; padding: 30px; text-align: center; max-width: 480px; box-shadow: 0 8px 24px rgba(0,0,0,0.5); }}
                    h2 {{ color: #F44336; margin-top: 0; }}
                    p {{ font-size: 0.9rem; color: #8B949E; line-height: 1.5; }}
                    a {{ color: #2F81F7; text-decoration: none; font-weight: bold; }}
                </style>
            </head>
            <body>
                <div class="card">
                    <h2>❌ Authorization Cancelled or Failed</h2>
                    <p><b>{error}</b>: {error_description}</p>
                    <p style="margin-top: 20px;"><a href="/">⬅ Return to Dashboard</a></p>
                </div>
            </body>
            </html>
            """
            return render_template_string(html_content), 400

        if not code or not state:
            return "Missing authorization code or state parameter", 400

        success, msg = coordinator.complete_pkce_login(code, state)
        if success:
            html_content = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>NinjaOne Authenticated</title>
                <meta http-equiv="refresh" content="2; url=/" />
                <style>
                    body { font-family: 'Segoe UI', sans-serif; background: #0D1117; color: #E6EDF3; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
                    .card { background: #161B22; border: 1px solid #00C853; border-radius: 12px; padding: 36px; text-align: center; max-width: 480px; box-shadow: 0 8px 24px rgba(0,0,0,0.5); }
                    h2 { color: #00C853; margin-top: 0; }
                    .spinner { border: 4px solid rgba(255,255,255,0.1); width: 36px; height: 36px; border-radius: 50%; border-left-color: #2F81F7; animation: spin 1s linear infinite; margin: 20px auto; }
                    @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
                    p { font-size: 0.9rem; color: #8B949E; }
                    a { color: #2F81F7; text-decoration: none; font-weight: bold; }
                </style>
            </head>
            <body>
                <div class="card">
                    <h2>✅ Sign-In Successful!</h2>
                    <p>Authenticated with NinjaOne via OAuth 2.0 PKCE.</p>
                    <div class="spinner"></div>
                    <p style="font-size: 0.85rem; color: #8B949E;">Redirecting to your live dashboard in 2 seconds...</p>
                    <p style="margin-top: 15px;"><a href="/">Click here if not redirected automatically</a></p>
                </div>
            </body>
            </html>
            """
            return render_template_string(html_content)
        else:
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>NinjaOne Authentication Error</title>
                <style>
                    body {{ font-family: 'Segoe UI', sans-serif; background: #0D1117; color: #E6EDF3; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }}
                    .card {{ background: #161B22; border: 1px solid #F44336; border-radius: 10px; padding: 30px; text-align: center; max-width: 480px; box-shadow: 0 8px 24px rgba(0,0,0,0.5); }}
                    h2 {{ color: #F44336; margin-top: 0; }}
                    p {{ font-size: 0.9rem; color: #8B949E; line-height: 1.5; }}
                    a {{ color: #2F81F7; text-decoration: none; font-weight: bold; }}
                </style>
            </head>
            <body>
                <div class="card">
                    <h2>❌ Authentication Error</h2>
                    <p>{msg}</p>
                    <p style="margin-top: 20px;"><a href="/">⬅ Return to Dashboard</a></p>
                </div>
            </body>
            </html>
            """
            return render_template_string(html_content), 400

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
            method_str = "PKCE Browser Login" if coordinator.auth_method == "pkce" else "Client Credentials"
            console.print(f"[green]>> Live Mode Active ({method_str}) -- Connected to NinjaOne ({coordinator.base_url})[/green]")
        else:
            console.print("[yellow]>> Starting in Demo Mode (Connect anytime via Sign In button)[/yellow]")

    app = create_app(coordinator.get_dashboard_data)

    console.print(f"\n[bold green]Dashboard live at:[/bold green] http://localhost:{args.port}")
    console.print("[dim]Press Ctrl+C to exit.[/dim]\n")

    app.run(debug=args.debug, port=args.port, host="0.0.0.0")


if __name__ == "__main__":
    main()
