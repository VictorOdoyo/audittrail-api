from uuid import uuid4

from fastapi.testclient import TestClient

from audittrail_api.main import app

ADMIN_HEADERS = {"Authorization": "Bearer local-admin-token"}


def provision_application(client: TestClient) -> str:
    suffix = uuid4().hex[:8]
    organization = client.post(
        "/api/v1/organizations",
        headers=ADMIN_HEADERS,
        json={"name": "Key Test Tenant", "slug": f"key-test-{suffix}"},
    ).json()
    application = client.post(
        f"/api/v1/organizations/{organization['id']}/applications",
        headers=ADMIN_HEADERS,
        json={"name": "Event Source", "slug": "event-source"},
    ).json()
    return str(application["id"])


def test_api_key_is_issued_once_and_can_be_revoked() -> None:
    with TestClient(app) as client:
        application_id = provision_application(client)
        issue_response = client.post(
            f"/api/v1/applications/{application_id}/api-keys",
            headers=ADMIN_HEADERS,
            json={"name": "Production writer", "scopes": ["events:write", "events:write"]},
        )
        issued = issue_response.json()
        list_response = client.get(
            f"/api/v1/applications/{application_id}/api-keys", headers=ADMIN_HEADERS
        )
        revoke_response = client.delete(
            f"/api/v1/applications/{application_id}/api-keys/{issued['id']}",
            headers=ADMIN_HEADERS,
        )

    assert issue_response.status_code == 201
    assert issued["secret"].startswith("at_live_")
    assert "secret" not in list_response.json()[0]
    assert revoke_response.status_code == 204


def test_key_cannot_be_issued_for_unknown_application() -> None:
    with TestClient(app) as client:
        response = client.post(
            f"/api/v1/applications/{uuid4()}/api-keys",
            headers=ADMIN_HEADERS,
            json={"name": "Unknown key", "scopes": ["events:read"]},
        )

    assert response.status_code == 404


def test_invalid_api_key_is_rejected() -> None:
    with TestClient(app) as client:
        missing = client.get("/api/v1/events")
        malformed = client.get("/api/v1/events", headers={"X-API-Key": "too-short"})
        unknown = client.get("/api/v1/events", headers={"X-API-Key": "at_live_unknown-secret"})

    assert missing.status_code == 401
    assert malformed.status_code == 401
    assert unknown.status_code == 401


def test_revoked_api_key_cannot_authenticate() -> None:
    with TestClient(app) as client:
        application_id = provision_application(client)
        issued = client.post(
            f"/api/v1/applications/{application_id}/api-keys",
            headers=ADMIN_HEADERS,
            json={"name": "Temporary reader", "scopes": ["events:read"]},
        ).json()
        client.delete(
            f"/api/v1/applications/{application_id}/api-keys/{issued['id']}",
            headers=ADMIN_HEADERS,
        )
        response = client.get("/api/v1/events", headers={"X-API-Key": issued["secret"]})

    assert response.status_code == 401
