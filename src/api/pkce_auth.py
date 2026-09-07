"""
OAuth 2.0 PKCE (Proof Key for Code Exchange) Authentication Engine for NinjaOne.

Implements RFC 7636 Authorization Code flow with S256 Code Challenge:
- Generates cryptographically secure code verifier, challenge, and state tokens
- Uses official NinjaOne OAuth endpoints: /ws/oauth/authorize and /ws/oauth/token
- Requests scopes: monitoring, management, offline_access
- Automatic Loopback Callback Listener for any custom redirect port (e.g. 11434, 8050)
- Automatically refreshes expired tokens using the refresh_token grant
"""

from __future__ import annotations

import base64
import hashlib
import http.server
import json
import os
import secrets
import socketserver
import threading
import time
from typing import Any, Dict, Optional, Tuple
from urllib.parse import parse_qs, urlencode, urljoin, urlparse

import requests
from rich.console import Console

from src.utils.ssl_helper import get_ssl_verify

console = Console()

DEFAULT_SCOPES = ["monitoring", "management", "offline_access"]


class _LoopbackCallbackHandler(http.server.BaseHTTPRequestHandler):
    """Temporary local HTTP handler to capture OAuth2 redirect code on loopback ports."""

    auth_manager: Optional[PKCEAuthManager] = None

    def log_message(self, format, *args):
        # Silence default HTTP server logging
        pass

    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        code = params.get("code", [None])[0]
        state = params.get("state", [None])[0]
        error = params.get("error", [None])[0]
        error_desc = params.get("error_description", [""])[0]

        if error:
            self.send_response(400)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            html_page = f"""
            <!DOCTYPE html>
            <html>
            <head><title>NinjaOne Login Failed</title>
            <style>body {{ font-family: sans-serif; background: #0D1117; color: #E6EDF3; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }}
            .card {{ background: #161B22; border: 1px solid #F44336; border-radius: 12px; padding: 30px; text-align: center; max-width: 480px; }}
            h2 {{ color: #F44336; }} a {{ color: #2F81F7; }}</style></head>
            <body><div class="card"><h2>❌ Authorization Failed</h2><p>{error}: {error_desc}</p><p><a href="http://localhost:8050/">Return to Dashboard</a></p></div></body></html>
            """
            self.wfile.write(html_page.encode("utf-8"))
            return

        if not code or not state:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Missing authorization code or state.")
            return

        if self.auth_manager:
            success, msg, data = self.auth_manager.handle_callback(code, state)
            if success:
                # Notify coordinator
                try:
                    from src.metrics.data_provider import coordinator
                    coordinator._init_live_client_if_configured()
                except Exception:
                    pass

                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                html_page = """
                <!DOCTYPE html>
                <html>
                <head>
                    <title>NinjaOne Authenticated</title>
                    <meta http-equiv="refresh" content="1; url=http://localhost:8050/" />
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
                        <p style="font-size: 0.85rem; color: #8B949E;">Redirecting to your live dashboard in 1 second...</p>
                        <p style="margin-top: 15px;"><a href="http://localhost:8050/">Click here if not redirected automatically</a></p>
                    </div>
                </body>
                </html>
                """
                self.wfile.write(html_page.encode("utf-8"))
            else:
                self.send_response(400)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                html_page = f"""
                <!DOCTYPE html>
                <html><head><title>NinjaOne Error</title>
                <style>body {{ font-family: sans-serif; background: #0D1117; color: #E6EDF3; display: flex; align-items: center; justify-content: center; height: 100vh; }}
                .card {{ background: #161B22; border: 1px solid #F44336; border-radius: 12px; padding: 30px; text-align: center; }}
                h2 {{ color: #F44336; }} a {{ color: #2F81F7; }}</style></head>
                <body><div class="card"><h2>❌ Error</h2><p>{msg}</p><p><a href="http://localhost:8050/">Return to Dashboard</a></p></div></body></html>
                """
                self.wfile.write(html_page.encode("utf-8"))


class PKCEAuthManager:
    """Manages PKCE state, token exchange, and persistent token caching."""

    def __init__(self):
        # In-memory storage for active pending authorization states: state -> dict
        self._pending_flows: Dict[str, Dict[str, Any]] = {}
        self._active_servers: Dict[int, socketserver.TCPServer] = {}

    @staticmethod
    def generate_code_verifier(length: int = 64) -> str:
        """Generate high-entropy cryptographic code verifier (RFC 7636)."""
        random_bytes = secrets.token_bytes(length)
        verifier = base64.urlsafe_b64encode(random_bytes).decode("ascii").rstrip("=")
        return verifier[:length]

    @staticmethod
    def generate_code_challenge(verifier: str) -> str:
        """Compute S256 code challenge from the verifier."""
        sha256_digest = hashlib.sha256(verifier.encode("ascii")).digest()
        challenge = base64.urlsafe_b64encode(sha256_digest).decode("ascii").rstrip("=")
        return challenge

    @staticmethod
    def generate_state() -> str:
        """Generate cryptographically secure CSRF protection token."""
        return secrets.token_urlsafe(24)

    def _start_loopback_listener_if_needed(self, redirect_uri: str) -> None:
        """Starts a temporary local background server on the redirect port if not 8050."""
        try:
            parsed = urlparse(redirect_uri)
            port = parsed.port or (443 if parsed.scheme == "https" else 80)
            host = parsed.hostname or "127.0.0.1"

            # If it's already port 8050, the main Dash server handles it
            if port == 8050:
                return

            if port in self._active_servers:
                return

            handler_class = _LoopbackCallbackHandler
            handler_class.auth_manager = self

            class _ReusableTCPServer(socketserver.TCPServer):
                allow_reuse_address = True

            server = _ReusableTCPServer((host, port), handler_class)
            self._active_servers[port] = server

            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            console.log(f"[green]Started background OAuth loopback listener on http://{host}:{port}[/green]")
        except Exception as e:
            console.log(f"[yellow]Note: Loopback listener on {redirect_uri} could not start (might already be bound): {e}[/yellow]")

    def initiate_flow(
        self,
        base_url: str,
        client_id: str,
        redirect_uri: str = "http://127.0.0.1:11434",
        scopes: Optional[list[str]] = None,
    ) -> Tuple[str, str]:
        """
        Initiates a PKCE authorization flow using official NinjaOne OAuth endpoints.

        Returns:
            (authorization_url, state)
        """
        base_url = (base_url or "https://app.ninjarmm.com").strip().rstrip("/")
        if not base_url.startswith("http"):
            base_url = f"https://{base_url}"

        verifier = self.generate_code_verifier()
        challenge = self.generate_code_challenge(verifier)
        state = self.generate_state()
        scope_str = " ".join(scopes or DEFAULT_SCOPES)

        # Start auxiliary listener on loopback port (e.g. 11434)
        self._start_loopback_listener_if_needed(redirect_uri)

        # Store pending parameters indexed by state
        self._pending_flows[state] = {
            "base_url": base_url,
            "client_id": client_id,
            "verifier": verifier,
            "redirect_uri": redirect_uri,
            "created_at": time.time(),
        }

        # Build official NinjaOne authorization endpoint URL
        auth_endpoint = f"{base_url}/ws/oauth/authorize"
        params = {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": scope_str,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "state": state,
        }
        auth_url = f"{auth_endpoint}?{urlencode(params)}"
        return auth_url, state

    def handle_callback(self, code: str, state: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Validates state and exchanges authorization code for tokens.

        Returns:
            (success, message, token_data)
        """
        flow = self._pending_flows.pop(state, None)
        if not flow:
            return False, "Invalid or expired authorization state. Please try logging in again.", None

        base_url = flow["base_url"]
        client_id = flow["client_id"]
        verifier = flow["verifier"]
        redirect_uri = flow["redirect_uri"]

        # Official token endpoint
        token_endpoint = f"{base_url}/ws/oauth/token"
        payload = {
            "grant_type": "authorization_code",
            "client_id": client_id,
            "code": code,
            "code_verifier": verifier,
            "redirect_uri": redirect_uri,
        }

        try:
            headers = {
                "User-Agent": "NinjaOne-Infra-Dashboard",
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
            }
            resp = requests.post(token_endpoint, data=payload, headers=headers, timeout=20, verify=get_ssl_verify())
            
            # Fallback to /oauth/token if /ws/oauth/token returned 404
            if resp.status_code == 404:
                token_endpoint_alt = f"{base_url}/oauth/token"
                resp = requests.post(token_endpoint_alt, data=payload, headers=headers, timeout=20, verify=get_ssl_verify())

            if resp.status_code != 200:
                return False, f"Token exchange failed ({resp.status_code}): {resp.text}", None

            data = resp.json()
            data["base_url"] = base_url
            data["client_id"] = client_id
            data["auth_method"] = "pkce"
            data["expires_at"] = time.time() + data.get("expires_in", 3600)

            # Persist tokens to local cache
            self.save_token_data(data)
            return True, "Successfully authenticated with NinjaOne via PKCE!", data

        except Exception as e:
            return False, f"Error communicating with NinjaOne: {str(e)}", None

    def refresh_token(self, token_data: Dict[str, Any]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Refreshes an existing access token using its refresh_token."""
        refresh_token = token_data.get("refresh_token")
        base_url = token_data.get("base_url") or os.getenv("NINJA_BASE_URL", "https://app.ninjarmm.com")
        client_id = token_data.get("client_id") or os.getenv("NINJA_CLIENT_ID", "")

        if not refresh_token:
            return False, "No refresh token available.", None

        token_endpoint = f"{base_url}/ws/oauth/token"
        payload = {
            "grant_type": "refresh_token",
            "client_id": client_id,
            "refresh_token": refresh_token,
        }

        try:
            headers = {
                "User-Agent": "NinjaOne-Infra-Dashboard",
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
            }
            resp = requests.post(token_endpoint, data=payload, headers=headers, timeout=20, verify=get_ssl_verify())
            if resp.status_code == 404:
                token_endpoint_alt = f"{base_url}/oauth/token"
                resp = requests.post(token_endpoint_alt, data=payload, headers=headers, timeout=20, verify=get_ssl_verify())

            if resp.status_code != 200:
                return False, f"Token refresh failed ({resp.status_code}): {resp.text}", None

            new_data = resp.json()
            new_data["base_url"] = base_url
            new_data["client_id"] = client_id
            new_data["auth_method"] = "pkce"
            new_data["expires_at"] = time.time() + new_data.get("expires_in", 3600)
            if "refresh_token" not in new_data:
                new_data["refresh_token"] = refresh_token

            self.save_token_data(new_data)
            return True, "Token refreshed successfully.", new_data

        except Exception as e:
            return False, f"Token refresh error: {str(e)}", None

    def save_token_data(self, token_data: Dict[str, Any]) -> None:
        """Saves active PKCE token cache to .env and runtime memory."""
        env_path = os.path.join(os.getcwd(), ".env")
        lines = []
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

        keys_to_update = {
            "NINJA_BASE_URL": token_data.get("base_url", ""),
            "NINJA_CLIENT_ID": token_data.get("client_id", ""),
            "NINJA_AUTH_METHOD": "pkce",
            "NINJA_PKCE_ACCESS_TOKEN": token_data.get("access_token", ""),
            "NINJA_PKCE_REFRESH_TOKEN": token_data.get("refresh_token", ""),
            "NINJA_PKCE_EXPIRES_AT": str(int(token_data.get("expires_at", 0))),
            "DEMO_MODE": "false",
        }

        keys_to_update["NINJA_CLIENT_SECRET"] = ""

        for k, v in keys_to_update.items():
            os.environ[k] = v

        written_keys = set()
        new_lines = []
        for line in lines:
            stripped = line.strip()
            if "=" in stripped and not stripped.startswith("#"):
                key = stripped.split("=")[0].strip()
                if key in keys_to_update:
                    new_lines.append(f"{key}={keys_to_update[key]}\n")
                    written_keys.add(key)
                    continue
            new_lines.append(line)

        for key, val in keys_to_update.items():
            if key not in written_keys:
                new_lines.append(f"{key}={val}\n")

        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

    def load_cached_token(self) -> Optional[Dict[str, Any]]:
        """Loads cached PKCE tokens from environment if valid."""
        access_token = os.getenv("NINJA_PKCE_ACCESS_TOKEN")
        refresh_token = os.getenv("NINJA_PKCE_REFRESH_TOKEN")
        base_url = os.getenv("NINJA_BASE_URL", "https://app.ninjarmm.com")
        client_id = os.getenv("NINJA_CLIENT_ID", "")
        expires_at = float(os.getenv("NINJA_PKCE_EXPIRES_AT", "0"))

        if access_token or refresh_token:
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "base_url": base_url,
                "client_id": client_id,
                "expires_at": expires_at,
                "auth_method": "pkce",
            }
        return None

    def clear_tokens(self) -> None:
        """Clears all stored tokens and resets environment."""
        for key in ["NINJA_PKCE_ACCESS_TOKEN", "NINJA_PKCE_REFRESH_TOKEN", "NINJA_PKCE_EXPIRES_AT", "NINJA_AUTH_METHOD"]:
            os.environ.pop(key, None)

        env_path = os.path.join(os.getcwd(), ".env")
        if os.path.exists(env_path):
            lines = []
            with open(env_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            new_lines = [l for l in lines if not any(l.startswith(k) for k in ["NINJA_PKCE_", "NINJA_AUTH_METHOD"])]
            with open(env_path, "w", encoding="utf-8") as f:
                f.writelines(new_lines)


# Singleton PKCE manager instance
pkce_manager = PKCEAuthManager()
