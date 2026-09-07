"""Tests for the NinjaOne API client."""

import pytest
import responses as responses_lib
from responses import matchers

from src.api.client import NinjaOneClient, NinjaAuthError, NinjaAPIError


MOCK_BASE = "https://app.ninjarmm.com"
MOCK_TOKEN_URL = f"{MOCK_BASE}/oauth/token"


def _mock_token(rsps):
    rsps.add(
        responses_lib.POST,
        MOCK_TOKEN_URL,
        json={"access_token": "test-token-abc", "expires_in": 3600},
        status=200,
    )


@pytest.fixture
def client():
    return NinjaOneClient(
        base_url=MOCK_BASE,
        client_id="test-client",
        client_secret="test-secret",
    )


@responses_lib.activate
def test_get_devices_success(client):
    _mock_token(responses_lib)
    responses_lib.add(
        responses_lib.GET,
        f"{MOCK_BASE}/v2/devices",
        json=[{"id": 1, "organizationId": 10, "offline": False}],
        status=200,
    )
    result = client.get("/v2/devices")
    assert isinstance(result, list)
    assert result[0]["id"] == 1


@responses_lib.activate
def test_get_raises_on_404(client):
    _mock_token(responses_lib)
    responses_lib.add(
        responses_lib.GET,
        f"{MOCK_BASE}/v2/device/9999",
        json={"error": "not found"},
        status=404,
    )
    with pytest.raises(NinjaAPIError) as exc_info:
        client.get("/v2/device/9999")
    assert exc_info.value.status_code == 404


@responses_lib.activate
def test_auth_error_on_bad_token():
    responses_lib.add(
        responses_lib.POST,
        MOCK_TOKEN_URL,
        json={"error": "invalid_client"},
        status=401,
    )
    client = NinjaOneClient(
        base_url=MOCK_BASE,
        client_id="bad",
        client_secret="bad",
    )
    with pytest.raises(NinjaAuthError):
        client.get("/v2/devices")


@responses_lib.activate
def test_paginated_get_single_page(client):
    _mock_token(responses_lib)
    responses_lib.add(
        responses_lib.GET,
        f"{MOCK_BASE}/v2/devices",
        json=[{"id": i, "organizationId": 1} for i in range(5)],
        status=200,
    )
    result = client.paginated_get("/v2/devices", page_size=500)
    assert len(result) == 5


@responses_lib.activate
def test_paginated_get_multi_page(client):
    _mock_token(responses_lib)
    # Page 1: 3 items (page_size=3)
    responses_lib.add(
        responses_lib.GET,
        f"{MOCK_BASE}/v2/devices",
        json=[{"id": 1, "name": "d1"}, {"id": 2, "name": "d2"}, {"id": 3, "name": "d3"}],
        status=200,
    )
    # Page 2: 2 items (last page)
    responses_lib.add(
        responses_lib.GET,
        f"{MOCK_BASE}/v2/devices",
        json=[{"id": 4, "name": "d4"}, {"id": 5, "name": "d5"}],
        status=200,
    )
    result = client.paginated_get("/v2/devices", page_size=3)
    assert len(result) == 5
    assert [d["id"] for d in result] == [1, 2, 3, 4, 5]
