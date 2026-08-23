"""API wrappers for /v2/organizations."""

from __future__ import annotations

from src.api.client import NinjaOneClient
from src.api.models import Organization, OrganizationSummary


def get_organizations(client: NinjaOneClient) -> list[OrganizationSummary]:
    """Fetch all organizations (brief)."""
    raw = client.paginated_get("/v2/organizations")
    return [OrganizationSummary.model_validate(o) for o in raw if isinstance(o, dict)]


def get_organizations_detailed(client: NinjaOneClient) -> list[Organization]:
    """Fetch all organizations with device counts and metadata."""
    raw = client.paginated_get("/v2/organizations-detailed")
    return [Organization.model_validate(o) for o in raw if isinstance(o, dict)]


def get_organization(client: NinjaOneClient, org_id: int) -> Organization:
    """Fetch a single organization by ID."""
    raw = client.get(f"/v2/organization/{org_id}")
    return Organization.model_validate(raw)


def get_organization_devices(client: NinjaOneClient, org_id: int) -> list[dict]:
    """Fetch devices belonging to a specific organization."""
    return client.paginated_get(f"/v2/organization/{org_id}/devices")
