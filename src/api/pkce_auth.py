"""
OAuth 2.0 PKCE (Proof Key for Code Exchange) Authentication Engine for NinjaOne.

Implements RFC 7636 Authorization Code flow with S256 Code Challenge:
- Generates cryptographically secure code verifier, challenge, and state tokens
- Builds browser authorization redirect URLs
- Exchanges authorization codes for access and refresh tokens without requiring a client secret
- Automatically refreshes expired tokens using the refresh_token grant
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import time
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlencode, urljoin

import requests
from rich.console import Console

console = Console()

DEFAULT_SCOPES = ["monitoring", "management"]


class PKCEAuthManager:
    """Manages PKCE state, token exchange, and persistent token caching."""

    def __init__(self):
        # In-memory storage for active pending authorization states: state -> dict
        self._pending_flows: Dict[str, Dict[str, Any]] = {}

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

    def initiate_flow(
        self,
        base_url: str,
        client_id: str,
        redirect_uri: str = "http://localhost:8050/oauth/callback",
        scopes: Optional[list[str]] = None,
    ) -> Tuple[str, str]:
        """
        Initiates a PKCE authorization flow.

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

        # Store pending parameters indexed by state
        self._pending_flows[state] = {
            "base_url": base_url,
            "client_id": client_id,
            "verifier": verifier,
            "redirect_uri": redirect_uri,
            "created_at": time.time(),
        }

        # Build authorization endpoint URL
        auth_endpoint = urljoin(base_url, "/oauth/authorize")
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

        token_endpoint = urljoin(base_url, "/oauth/token")
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
            }
            resp = requests.post(token_endpoint, data=payload, headers=headers, timeout=20)
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

        token_endpoint = urljoin(base_url, "/oauth/token")
        payload = {
            "grant_type": "refresh_token",
            "client_id": client_id,
            "refresh_token": refresh_token,
        }

        try:
            headers = {
                "User-Agent": "NinjaOne-Infra-Dashboard",
                "Content-Type": "application/x-www-form-urlencoded",
            }
            resp = requests.post(token_endpoint, data=payload, headers=headers, timeout=20)
            if resp.status_code != 200:
                return False, f"Token refresh failed ({resp.status_code}): {resp.text}", None

            new_data = resp.json()
            new_data["base_url"] = base_url
            new_data["client_id"] = client_id
            new_data["auth_method"] = "pkce"
            new_data["expires_at"] = time.time() + new_data.get("expires_in", 3600)
            # If server doesn't return new refresh_token, keep previous one
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
        }

        # Clear client secret if using PKCE
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
