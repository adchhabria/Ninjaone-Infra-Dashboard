"""
Dynamic Data Provider & Connection Coordinator for NinjaOne Dashboard.

Manages switching between:
1. Live NinjaOne REST API data:
   - OAuth 2.0 PKCE Authorization Code flow (Browser login - No Client Secret required)
   - OAuth 2.0 Client Credentials flow (Headless / M2M Client ID + Client Secret)
2. Realistic Demo/Sample data (when unauthenticated or in Demo Mode).

Provides live connection testing, browser PKCE sign-in, and sign-out capabilities.
"""

from __future__ import annotations

import os
import time
from typing import Any, Optional, Tuple

from dotenv import load_dotenv

from scripts.generate_sample_data import get_mock_dashboard_data
from src.metrics.aggregator import DashboardData


class DataCoordinator:
    """Coordinates data fetching between Live NinjaOne API and Mock/Sample dataset."""

    def __init__(self):
        load_dotenv()
        self._aggregator = None
        self._client = None
        self._is_live = False
        self._last_error = None
        self._auth_method = "client_credentials"
        self._init_live_client_if_configured()

    def _init_live_client_if_configured(self):
        """Attempts to initialize live NinjaOneClient from PKCE cache or environment variables."""
        from src.api.pkce_auth import pkce_manager
        from src.api.client import NinjaOneClient
        from src.metrics.aggregator import MetricsAggregator

        demo_forced = os.getenv("DEMO_MODE", "false").lower() == "true"
        if demo_forced:
            self._is_live = False
            self._client = None
            self._aggregator = None
            return

        cache_ttl = int(os.getenv("CACHE_TTL_SECONDS", 300))

        # 1. Try PKCE cached token
        cached_pkce = pkce_manager.load_cached_token()
        if cached_pkce and cached_pkce.get("access_token"):
            try:
                client = NinjaOneClient.from_pkce(
                    base_url=cached_pkce.get("base_url") or self.base_url,
                    client_id=cached_pkce.get("client_id") or os.getenv("NINJA_CLIENT_ID", ""),
                    token_data=cached_pkce,
                )
                # Verify token works
                _ = client._tokens.get_token()
                self._client = client
                self._aggregator = MetricsAggregator(client, cache_ttl=cache_ttl)
                self._is_live = True
                self._auth_method = "pkce"
                self._last_error = None
                print(f"[+] Live NinjaOne PKCE Connection Active: {self.base_url}")
                return
            except Exception as e:
                print(f"[!] PKCE Cached Connection Failed: {e}")

        # 2. Try Client Credentials
        client_id = os.getenv("NINJA_CLIENT_ID", "").strip()
        client_secret = os.getenv("NINJA_CLIENT_SECRET", "").strip()
        base_url = os.getenv("NINJA_BASE_URL", "https://app.ninjarmm.com").strip().rstrip("/")

        if client_id and client_secret:
            try:
                client = NinjaOneClient(base_url=base_url, client_id=client_id, client_secret=client_secret)
                _ = client._tokens.get_token()
                self._client = client
                self._aggregator = MetricsAggregator(client, cache_ttl=cache_ttl)
                self._is_live = True
                self._auth_method = "client_credentials"
                self._last_error = None
                print(f"[+] Live NinjaOne Client Credentials Connection Active: {base_url}")
                return
            except Exception as e:
                self._is_live = False
                self._client = None
                self._aggregator = None
                self._last_error = str(e)
                print(f"[!] NinjaOne Live Connection Initialization Failed: {e}")
                return

        self._is_live = False
        self._client = None
        self._aggregator = None

    @property
    def is_live(self) -> bool:
        return self._is_live

    @property
    def auth_method(self) -> str:
        return self._auth_method if self._is_live else "none"

    @property
    def base_url(self) -> str:
        return os.getenv("NINJA_BASE_URL", "https://app.ninjarmm.com")

    @property
    def client_id(self) -> str:
        return os.getenv("NINJA_CLIENT_ID", "")

    @property
    def client_id_masked(self) -> str:
        cid = os.getenv("NINJA_CLIENT_ID", "")
        if len(cid) > 8:
            return f"{cid[:4]}...{cid[-4:]}"
        return cid

    # -----------------------------------------------------------------------
    # PKCE Browser Authorization Methods
    # -----------------------------------------------------------------------

    def initiate_pkce_login(
        self,
        base_url: str,
        client_id: str,
        redirect_uri: str = "http://localhost:8050/oauth/callback",
    ) -> Tuple[str, str]:
        """
        Initiates the OAuth 2.0 PKCE browser authorization flow.
        Returns (auth_url, state).
        """
        from src.api.pkce_auth import pkce_manager
        return pkce_manager.initiate_flow(base_url=base_url, client_id=client_id, redirect_uri=redirect_uri)

    def complete_pkce_login(self, code: str, state: str) -> Tuple[bool, str]:
        """
        Exchanges the authorization code for tokens, saves tokens, and switches to LIVE mode.
        """
        from src.api.pkce_auth import pkce_manager
        from src.api.client import NinjaOneClient
        from src.metrics.aggregator import MetricsAggregator

        success, msg, token_data = pkce_manager.handle_callback(code, state)
        if not success or not token_data:
            return False, msg

        try:
            base_url = token_data.get("base_url", self.base_url)
            client_id = token_data.get("client_id", self.client_id)
            cache_ttl = int(os.getenv("CACHE_TTL_SECONDS", 300))

            client = NinjaOneClient.from_pkce(base_url=base_url, client_id=client_id, token_data=token_data)
            self._client = client
            self._aggregator = MetricsAggregator(client, cache_ttl=cache_ttl)
            self._is_live = True
            self._auth_method = "pkce"
            self._last_error = None
            os.environ["DEMO_MODE"] = "false"

            print(f"[+] PKCE Live Login Completed Successfully for {base_url}")
            return True, "Successfully signed in via NinjaOne PKCE!"
        except Exception as e:
            return False, f"Failed to initialize metrics aggregator: {str(e)}"

    # -----------------------------------------------------------------------
    # Client Credentials Methods
    # -----------------------------------------------------------------------

    def test_connection(self, base_url: str, client_id: str, client_secret: str) -> Tuple[bool, str]:
        """
        Tests credentials directly against NinjaOne API /oauth/token.
        Returns (success: bool, message: str).
        """
        if not client_id or not client_secret:
            return False, "Client ID and Client Secret are required."

        base_url = (base_url or "https://app.ninjarmm.com").strip().rstrip("/")
        if not base_url.startswith("http"):
            base_url = f"https://{base_url}"

        try:
            from src.api.client import NinjaOneClient

            test_client = NinjaOneClient(
                base_url=base_url,
                client_id=client_id.strip(),
                client_secret=client_secret.strip(),
            )
            token = test_client._tokens.get_token()
            if not token:
                return False, "Failed to retrieve access token from NinjaOne OAuth endpoint."

            devices_resp = test_client.get("/v2/devices", params={"pageSize": 10})
            device_count = len(devices_resp) if isinstance(devices_resp, list) else 0

            return True, f"Successfully authenticated with NinjaOne! API Token acquired ({device_count}+ devices detected)."
        except Exception as e:
            err_msg = str(e)
            if "401" in err_msg or "invalid_client" in err_msg:
                return False, "Authentication Failed (401 / invalid_client): Please verify your Client ID, Client Secret, and Region URL."
            elif "403" in err_msg:
                return False, "Permission Denied (403): Ensure your API Client has the 'Monitoring' and 'Management' scopes enabled."
            return False, f"Connection Failed: {err_msg}"

    def sign_in(self, base_url: str, client_id: str, client_secret: str) -> Tuple[bool, str]:
        """Saves credentials, initializes live aggregator, and switches mode to LIVE."""
        success, msg = self.test_connection(base_url, client_id, client_secret)
        if not success:
            return False, msg

        base_url = (base_url or "https://app.ninjarmm.com").strip().rstrip("/")
        if not base_url.startswith("http"):
            base_url = f"https://{base_url}"

        os.environ["NINJA_BASE_URL"] = base_url
        os.environ["NINJA_CLIENT_ID"] = client_id.strip()
        os.environ["NINJA_CLIENT_SECRET"] = client_secret.strip()
        os.environ["NINJA_AUTH_METHOD"] = "client_credentials"
        os.environ["DEMO_MODE"] = "false"

        self._save_to_env_file(base_url, client_id.strip(), client_secret.strip())
        self._init_live_client_if_configured()
        return True, msg

    def sign_out(self):
        """Clears all active credentials (PKCE and Client Secret) and reverts to Demo dataset."""
        from src.api.pkce_auth import pkce_manager

        pkce_manager.clear_tokens()
        os.environ.pop("NINJA_CLIENT_ID", None)
        os.environ.pop("NINJA_CLIENT_SECRET", None)
        os.environ.pop("NINJA_AUTH_METHOD", None)
        os.environ["DEMO_MODE"] = "true"

        self._save_to_env_file(os.getenv("NINJA_BASE_URL", "https://app.ninjarmm.com"), "", "")
        self._is_live = False
        self._client = None
        self._aggregator = None
        self._auth_method = "none"

    def _save_to_env_file(self, base_url: str, client_id: str, client_secret: str, redirect_uri: Optional[str] = None, ssl_verify: Optional[str] = None):
        env_path = os.path.join(os.getcwd(), ".env")
        lines = []
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

        keys_written = set()
        new_lines = []
        for line in lines:
            if line.startswith("NINJA_BASE_URL="):
                new_lines.append(f"NINJA_BASE_URL={base_url}\n")
                keys_written.add("NINJA_BASE_URL")
            elif line.startswith("NINJA_CLIENT_ID="):
                new_lines.append(f"NINJA_CLIENT_ID={client_id}\n")
                keys_written.add("NINJA_CLIENT_ID")
            elif line.startswith("NINJA_CLIENT_SECRET="):
                new_lines.append(f"NINJA_CLIENT_SECRET={client_secret}\n")
                keys_written.add("NINJA_CLIENT_SECRET")
            elif redirect_uri and line.startswith("NINJA_REDIRECT_URI="):
                new_lines.append(f"NINJA_REDIRECT_URI={redirect_uri}\n")
                keys_written.add("NINJA_REDIRECT_URI")
            elif ssl_verify and line.startswith("NINJA_SSL_VERIFY="):
                new_lines.append(f"NINJA_SSL_VERIFY={ssl_verify}\n")
                keys_written.add("NINJA_SSL_VERIFY")
            elif line.startswith("DEMO_MODE="):
                new_lines.append(f"DEMO_MODE={'false' if client_id else 'true'}\n")
                keys_written.add("DEMO_MODE")
            else:
                new_lines.append(line)

        if "NINJA_BASE_URL" not in keys_written:
            new_lines.append(f"NINJA_BASE_URL={base_url}\n")
        if "NINJA_CLIENT_ID" not in keys_written:
            new_lines.append(f"NINJA_CLIENT_ID={client_id}\n")
        if "NINJA_CLIENT_SECRET" not in keys_written:
            new_lines.append(f"NINJA_CLIENT_SECRET={client_secret}\n")
        if redirect_uri and "NINJA_REDIRECT_URI" not in keys_written:
            new_lines.append(f"NINJA_REDIRECT_URI={redirect_uri}\n")
        if ssl_verify and "NINJA_SSL_VERIFY" not in keys_written:
            new_lines.append(f"NINJA_SSL_VERIFY={ssl_verify}\n")
        if "DEMO_MODE" not in keys_written:
            new_lines.append(f"DEMO_MODE={'false' if client_id else 'true'}\n")

        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

    def get_dashboard_data(
        self,
        active_org_id: Optional[int] = None,
        active_region: Optional[str] = None,
        active_location: Optional[str] = None,
        active_os_family: Optional[str] = None,
        force_refresh: bool = False,
        approaching_days: int = 180,
    ) -> DashboardData:
        """
        Retrieves DashboardData from Live NinjaOne API if authenticated,
        otherwise seamlessly returns the high-fidelity sample dataset.
        """
        if self._is_live and self._aggregator:
            try:
                return self._aggregator.get_dashboard_data(
                    active_org_id=active_org_id,
                    active_region=active_region,
                    active_location=active_location,
                    active_os_family=active_os_family,
                    force_refresh=force_refresh,
                    approaching_days=approaching_days,
                )
            except Exception as e:
                print(f"[!] Live data fetch failed, falling back to sample dataset: {e}")

        # Fallback to mock data
        return get_mock_dashboard_data(
            active_org_id=active_org_id,
            active_region=active_region,
            active_location=active_location,
            active_os_family=active_os_family,
            approaching_days=approaching_days,
        )


# Global Singleton Coordinator
coordinator = DataCoordinator()
