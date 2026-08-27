"""
NinjaOne OAuth2 API Client.

Handles:
- OAuth2 Client Credentials flow (Client ID + Client Secret)
- OAuth2 PKCE Authorization Code flow (Client ID + Refresh Token) with automatic token refresh
- Configurable base URL (US, US2, EU, CA, OC regions)
- Retry with exponential backoff (via tenacity)
- Rate-limit-aware (respects 429 Retry-After headers)
- Structured logging via `rich`
"""

from __future__ import annotations

import os
import time
from typing import Any, Dict, Optional
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)
from urllib3.util.retry import Retry

from rich.console import Console

console = Console()

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class NinjaAuthError(Exception):
    """Raised when OAuth token acquisition fails."""


class NinjaAPIError(Exception):
    """Raised on non-retryable API errors (4xx except 429)."""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(f"HTTP {status_code}: {message}")


class NinjaRateLimitError(Exception):
    """Raised on 429 Too Many Requests — caller should back off."""


# ---------------------------------------------------------------------------
# Token Manager
# ---------------------------------------------------------------------------

class _TokenManager:
    """Fetches and caches the OAuth2 Bearer token (supports Client Credentials & PKCE)."""

    def __init__(
        self,
        token_url: str,
        client_id: str,
        client_secret: Optional[str] = None,
        scopes: Optional[list[str]] = None,
        auth_method: str = "client_credentials",
        token_data: Optional[Dict[str, Any]] = None,
    ):
        self._token_url = token_url
        self._client_id = client_id
        self._client_secret = client_secret or ""
        self._scopes = scopes or ["monitoring", "management"]
        self._auth_method = auth_method
        self._token_data = dict(token_data or {})

        self._access_token: Optional[str] = self._token_data.get("access_token")
        self._expires_at: float = float(self._token_data.get("expires_at", 0))

    def get_token(self) -> str:
        if self._access_token and time.time() < self._expires_at - 30:
            return self._access_token
        return self._refresh()

    def _refresh(self) -> str:
        if self._auth_method == "pkce" or self._token_data.get("refresh_token"):
            from src.api.pkce_auth import pkce_manager
            success, msg, new_data = pkce_manager.refresh_token(self._token_data)
            if not success or not new_data:
                raise NinjaAuthError(f"PKCE Token refresh failed: {msg}")
            self._token_data = new_data
            self._access_token = new_data["access_token"]
            self._expires_at = new_data["expires_at"]
            console.log("[green]NinjaOne PKCE OAuth token refreshed.[/green]")
            return self._access_token

        # Standard Client Credentials Flow
        payload = {
            "grant_type": "client_credentials",
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "scope": " ".join(self._scopes),
        }
        resp = requests.post(self._token_url, data=payload, timeout=15)
        if resp.status_code != 200:
            raise NinjaAuthError(
                f"Token refresh failed ({resp.status_code}): {resp.text}"
            )
        data = resp.json()
        self._access_token = data["access_token"]
        self._expires_at = time.time() + data.get("expires_in", 3600)
        console.log("[green]NinjaOne OAuth Client Credentials token refreshed.[/green]")
        return self._access_token


# ---------------------------------------------------------------------------
# HTTP Session Factory
# ---------------------------------------------------------------------------

def _build_session() -> requests.Session:
    """Create a requests Session with retry/backoff for transient errors."""
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


# ---------------------------------------------------------------------------
# Main Client
# ---------------------------------------------------------------------------

class NinjaOneClient:
    """
    Authenticated NinjaOne REST API v2 client.
    """

    DEFAULT_SCOPES = ["monitoring", "management", "control"]

    def __init__(
        self,
        base_url: str,
        client_id: str,
        client_secret: Optional[str] = None,
        scopes: Optional[list[str]] = None,
        auth_method: str = "client_credentials",
        token_data: Optional[Dict[str, Any]] = None,
    ):
        self._base_url = base_url.rstrip("/")
        token_url = f"{self._base_url}/oauth/token"
        self._tokens = _TokenManager(
            token_url=token_url,
            client_id=client_id,
            client_secret=client_secret,
            scopes=scopes or self.DEFAULT_SCOPES,
            auth_method=auth_method,
            token_data=token_data,
        )
        self._session = _build_session()

    # ------------------------------------------------------------------
    # Factories
    # ------------------------------------------------------------------

    @classmethod
    def from_env(cls) -> "NinjaOneClient":
        """Instantiate from environment variables (supports Client Credentials & PKCE)."""
        from dotenv import load_dotenv
        load_dotenv()

        base_url = os.getenv("NINJA_BASE_URL", "https://app.ninjarmm.com")
        client_id = os.getenv("NINJA_CLIENT_ID", "")
        client_secret = os.getenv("NINJA_CLIENT_SECRET", "")
        auth_method = os.getenv("NINJA_AUTH_METHOD", "client_credentials")

        # Check for PKCE cached token first
        from src.api.pkce_auth import pkce_manager
        cached_pkce = pkce_manager.load_cached_token()
        if cached_pkce and (auth_method == "pkce" or not client_secret):
            return cls(
                base_url=cached_pkce.get("base_url") or base_url,
                client_id=cached_pkce.get("client_id") or client_id,
                auth_method="pkce",
                token_data=cached_pkce,
            )

        if not client_id or not client_secret:
            raise NinjaAuthError(
                "NinjaOne credentials missing. Provide Client ID & Secret or authenticate with PKCE."
            )

        return cls(
            base_url=base_url,
            client_id=client_id,
            client_secret=client_secret,
            auth_method="client_credentials",
        )

    @classmethod
    def from_pkce(cls, base_url: str, client_id: str, token_data: Dict[str, Any]) -> "NinjaOneClient":
        """Instantiate directly from PKCE token response."""
        return cls(
            base_url=base_url,
            client_id=client_id,
            auth_method="pkce",
            token_data=token_data,
        )

    # ------------------------------------------------------------------
    # HTTP Methods
    # ------------------------------------------------------------------

    @retry(
        retry=retry_if_exception_type(NinjaRateLimitError),
        wait=wait_exponential(multiplier=2, min=2, max=60),
        stop=stop_after_attempt(5),
        reraise=True,
    )
    def get(self, endpoint: str, params: Optional[dict[str, Any]] = None) -> Any:
        """
        Execute an authenticated GET request.
        """
        url = urljoin(self._base_url, endpoint)
        token = self._tokens.get_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "User-Agent": "NinjaOne-Dashboard/1.0",
        }

        resp = self._session.get(url, params=params, headers=headers, timeout=30)

        if resp.status_code == 429:
            retry_after = int(resp.headers.get("Retry-After", 5))
            console.log(f"[yellow]Rate limit 429 encountered. Waiting {retry_after}s...[/yellow]")
            time.sleep(retry_after)
            raise NinjaRateLimitError()

        if resp.status_code == 401:
            console.log("[yellow]401 received -- forcing token refresh...[/yellow]")
            self._tokens._access_token = None
            token = self._tokens.get_token()
            headers["Authorization"] = f"Bearer {token}"
            resp = self._session.get(url, params=params, headers=headers, timeout=30)

        if not (200 <= resp.status_code < 300):
            raise NinjaAPIError(resp.status_code, resp.text)

        return resp.json()

    def get_paginated(
        self,
        endpoint: str,
        params: Optional[dict[str, Any]] = None,
        page_size: int = 100,
    ) -> list[Any]:
        """
        Fetch all pages of a paginated NinjaOne endpoint.
        """
        params = dict(params or {})
        params["pageSize"] = page_size
        results: list[Any] = []
        cursor: Optional[str] = None

        while True:
            if cursor:
                params["cursor"] = cursor
            data = self.get(endpoint, params=params)

            if isinstance(data, list):
                results.extend(data)
                break
            elif isinstance(data, dict):
                items = (
                    data.get("devices")
                    or data.get("results")
                    or data.get("activities")
                    or data.get("alerts")
                    or []
                )
                results.extend(items)
                cursor = data.get("cursor") or data.get("nextCursor")
                if not cursor or len(items) == 0:
                    break
            else:
                break

        return results

    # Alias for backward compatibility
    paginated_get = get_paginated
