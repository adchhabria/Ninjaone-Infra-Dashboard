"""
Unit tests for OAuth 2.0 PKCE authentication manager.
"""

from unittest.mock import MagicMock, patch
import pytest

from src.api.pkce_auth import PKCEAuthManager, pkce_manager


class TestPKCEAuth:
    def test_generate_code_verifier(self):
        verifier = PKCEAuthManager.generate_code_verifier(64)
        assert len(verifier) == 64
        assert isinstance(verifier, str)

    def test_generate_code_challenge(self):
        verifier = "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
        challenge = PKCEAuthManager.generate_code_challenge(verifier)
        assert isinstance(challenge, str)
        assert len(challenge) > 20
        # Deterministic check
        assert challenge == PKCEAuthManager.generate_code_challenge(verifier)

    def test_initiate_flow(self):
        mgr = PKCEAuthManager()
        auth_url, state = mgr.initiate_flow(
            base_url="https://app.ninjarmm.com",
            client_id="test_client_id_123",
            redirect_uri="http://localhost:8050/oauth/callback",
        )
        assert "https://app.ninjarmm.com/ws/oauth/authorize" in auth_url
        assert "client_id=test_client_id_123" in auth_url
        assert "response_type=code" in auth_url
        assert "code_challenge=" in auth_url
        assert "code_challenge_method=S256" in auth_url
        assert f"state={state}" in auth_url
        assert state in mgr._pending_flows

    @patch("requests.post")
    def test_handle_callback_success(self, mock_post):
        mgr = PKCEAuthManager()
        auth_url, state = mgr.initiate_flow(
            base_url="https://app.ninjarmm.com",
            client_id="test_client_id_123",
        )

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "access_token": "mock_access_token_123",
            "refresh_token": "mock_refresh_token_456",
            "expires_in": 3600,
            "token_type": "bearer",
        }
        mock_post.return_value = mock_resp

        success, msg, data = mgr.handle_callback(code="auth_code_xyz", state=state)
        assert success is True
        assert data is not None
        assert data["access_token"] == "mock_access_token_123"
        assert data["refresh_token"] == "mock_refresh_token_456"

    def test_handle_callback_invalid_state(self):
        mgr = PKCEAuthManager()
        success, msg, data = mgr.handle_callback(code="auth_code_xyz", state="non_existent_state")
        assert success is False
        assert data is None
        assert "Invalid or expired" in msg
