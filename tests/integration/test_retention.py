from uuid import uuid4

from fastapi.testclient import TestClient

from audittrail_api.main import app

ADMIN_HEADERS = {"Authorization": "Bearer local-admin-token"}


def create_organization(client: TestClient) -> str:
    suffix = uuid4().hex[:8]
    response = client.post(
        "/api/v1/organizations",
        headers=ADMIN_HEADERS,
        json={"name": "Retention Tenant", "slug": f"retention-{suffix}"},
    )
    return str(response.json()["id"])


def test_retention_policy_can_be_created_and_updated() -> None:
    with TestClient(app) as client:
        organization_id = create_organization(client)
        missing = client.get(
            f"/api/v1/organizations/{organization_id}/retention",
            headers=ADMIN_HEADERS,
        )
        created = client.put(
            f"/api/v1/organizations/{organization_id}/retention",
            headers=ADMIN_HEADERS,
            json={"retention_days": 365, "legal_hold": False, "updated_by": "admin-1"},
        )
        updated = client.put(
            f"/api/v1/organizations/{organization_id}/retention",
            headers=ADMIN_HEADERS,
            json={"retention_days": 730, "legal_hold": True, "updated_by": "auditor-2"},
        )

    assert missing.status_code == 404
    assert created.status_code == 200
    assert updated.json()["retention_days"] == 730
    assert updated.json()["legal_hold"] is True
    assert updated.json()["updated_by"] == "auditor-2"


def test_retention_policy_rejects_unsafe_window_and_unknown_tenant() -> None:
    with TestClient(app) as client:
        invalid = client.put(
            f"/api/v1/organizations/{uuid4()}/retention",
            headers=ADMIN_HEADERS,
            json={"retention_days": 1, "legal_hold": False, "updated_by": "admin-1"},
        )
        unknown = client.put(
            f"/api/v1/organizations/{uuid4()}/retention",
            headers=ADMIN_HEADERS,
            json={"retention_days": 365, "legal_hold": False, "updated_by": "admin-1"},
        )

    assert invalid.status_code == 422
    assert unknown.status_code == 404
