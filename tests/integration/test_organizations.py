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


def test_duplicate_organization_slug_conflicts() -> None:
    suffix = uuid4().hex[:8]
    payload = {"name": "Duplicate Tenant", "slug": f"duplicate-{suffix}"}
    with TestClient(app) as client:
        first = client.post("/api/v1/organizations", headers=ADMIN_HEADERS, json=payload)
        duplicate = client.post("/api/v1/organizations", headers=ADMIN_HEADERS, json=payload)
        listed = client.get("/api/v1/organizations", headers=ADMIN_HEADERS)

    assert first.status_code == 201
    assert duplicate.status_code == 409
    assert any(item["id"] == first.json()["id"] for item in listed.json())


def test_application_requires_existing_organization() -> None:
    with TestClient(app) as client:
        response = client.post(
            f"/api/v1/organizations/{uuid4()}/applications",
            headers=ADMIN_HEADERS,
            json={"name": "Unknown Source", "slug": "unknown-source"},
        )

    assert response.status_code == 404


def test_application_slug_is_unique_per_organization_and_apps_can_be_listed() -> None:
    suffix = uuid4().hex[:8]
    with TestClient(app) as client:
        organization = client.post(
            "/api/v1/organizations",
            headers=ADMIN_HEADERS,
            json={"name": "Application Tenant", "slug": f"application-{suffix}"},
        ).json()
        payload = {"name": "Access Service", "slug": "access-service"}
        first = client.post(
            f"/api/v1/organizations/{organization['id']}/applications",
            headers=ADMIN_HEADERS,
            json=payload,
        )
        duplicate = client.post(
            f"/api/v1/organizations/{organization['id']}/applications",
            headers=ADMIN_HEADERS,
            json=payload,
        )
        listed = client.get(
            f"/api/v1/organizations/{organization['id']}/applications",
            headers=ADMIN_HEADERS,
        )

    assert first.status_code == 201
    assert duplicate.status_code == 409
    assert [item["id"] for item in listed.json()] == [first.json()["id"]]
