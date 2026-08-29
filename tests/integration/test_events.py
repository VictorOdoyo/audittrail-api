from datetime import UTC, datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from audittrail_api.main import app

ADMIN_HEADERS = {"Authorization": "Bearer local-admin-token"}


def provision_key(client: TestClient, scopes: list[str]) -> str:
    suffix = uuid4().hex[:8]
    organization = client.post(
        "/api/v1/organizations",
        headers=ADMIN_HEADERS,
        json={"name": "Event Tenant", "slug": f"event-tenant-{suffix}"},
    ).json()
    application = client.post(
        f"/api/v1/organizations/{organization['id']}/applications",
        headers=ADMIN_HEADERS,
        json={"name": "Billing Service", "slug": "billing-service"},
    ).json()
    issued = client.post(
        f"/api/v1/applications/{application['id']}/api-keys",
        headers=ADMIN_HEADERS,
        json={"name": "Test credential", "scopes": scopes},
    ).json()
    return str(issued["secret"])


def make_event(event_id: str | None = None, action: str = "invoice.approved") -> dict[str, object]:
    return {
        "event_id": event_id or str(uuid4()),
        "occurred_at": datetime.now(UTC).isoformat(),
        "actor_type": "user",
        "actor_id": "user-42",
        "action": action,
        "resource_type": "invoice",
        "resource_id": "inv-100",
        "correlation_id": "request-200",
        "metadata": {"amount": 7500, "currency": "USD"},
    }


def test_event_ingestion_is_idempotent_and_searchable() -> None:
    with TestClient(app) as client:
        secret = provision_key(client, ["events:write", "events:read"])
        headers = {"X-API-Key": secret}
        payload = make_event()
        first = client.post("/api/v1/events", headers=headers, json=payload)
        retry = client.post("/api/v1/events", headers=headers, json=payload)
        search = client.get(
            "/api/v1/events", headers=headers, params={"action": "invoice.approved"}
        )

    assert first.status_code == 201
    assert retry.status_code == 200
    assert retry.json()["id"] == first.json()["id"]
    assert [item["id"] for item in search.json()["items"]] == [first.json()["id"]]


def test_reused_event_id_with_different_content_conflicts() -> None:
    with TestClient(app) as client:
        secret = provision_key(client, ["events:write"])
        headers = {"X-API-Key": secret}
        event_id = str(uuid4())
        client.post("/api/v1/events", headers=headers, json=make_event(event_id))
        conflict = client.post(
            "/api/v1/events",
            headers=headers,
            json=make_event(event_id, action="invoice.rejected"),
        )

    assert conflict.status_code == 409


def test_event_scope_is_enforced() -> None:
    with TestClient(app) as client:
        read_only_secret = provision_key(client, ["events:read"])
        response = client.post(
            "/api/v1/events",
            headers={"X-API-Key": read_only_secret},
            json=make_event(),
        )

    assert response.status_code == 403
