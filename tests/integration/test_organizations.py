from uuid import uuid4

from fastapi.testclient import TestClient

from audittrail_api.main import app

ADMIN_HEADERS = {"Authorization": "Bearer local-admin-token"}


def test_management_endpoints_require_admin_token() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/organizations")

    assert response.status_code == 401


def test_create_organization_and_application() -> None:
    suffix = uuid4().hex[:8]
    with TestClient(app) as client:
        organization_response = client.post(
            "/api/v1/organizations",
            headers=ADMIN_HEADERS,
            json={"name": "Northstar Security", "slug": f"northstar-{suffix}"},
        )
        organization_id = organization_response.json()["id"]
        application_response = client.post(
            f"/api/v1/organizations/{organization_id}/applications",
            headers=ADMIN_HEADERS,
            json={"name": "Access Console", "slug": "access-console"},
        )

    assert organization_response.status_code == 201
    assert application_response.status_code == 201
    assert application_response.json()["organization_id"] == organization_id
