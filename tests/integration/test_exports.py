import json
from datetime import UTC, datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from audittrail_api.main import app

ADMIN_HEADERS = {"Authorization": "Bearer local-admin-token"}


def provision_export_key(client: TestClient) -> str:
    suffix = uuid4().hex[:8]
    organization = client.post(
        "/api/v1/organizations",
        headers=ADMIN_HEADERS,
        json={"name": "Export Tenant", "slug": f"export-{suffix}"},
    ).json()
    application = client.post(
        f"/api/v1/organizations/{organization['id']}/applications",
        headers=ADMIN_HEADERS,
        json={"name": "Export Source", "slug": "export-source"},
    ).json()
    return str(
        client.post(
            f"/api/v1/applications/{application['id']}/api-keys",
            headers=ADMIN_HEADERS,
            json={
                "name": "Exporter",
                "scopes": ["events:write", "events:read", "exports:write"],
            },
        ).json()["secret"]
    )


def test_json_export_can_be_created_and_downloaded() -> None:
    with TestClient(app) as client:
        secret = provision_export_key(client)
        headers = {"X-API-Key": secret}
        client.post(
            "/api/v1/events",
            headers=headers,
            json={
                "event_id": str(uuid4()),
                "occurred_at": datetime.now(UTC).isoformat(),
                "actor_type": "service",
                "actor_id": "billing-worker",
                "action": "invoice.sent",
                "resource_type": "invoice",
                "resource_id": "inv-200",
                "metadata": {"currency": "USD"},
            },
        )
        created = client.post(
            "/api/v1/exports",
            headers=headers,
            json={"format": "json", "filters": {"action": "invoice.sent"}},
        )
        job = created.json()
        status_response = client.get(f"/api/v1/exports/{job['id']}", headers=headers)
        download = client.get(f"/api/v1/exports/{job['id']}/download", headers=headers)

    assert created.status_code == 201
    assert status_response.json()["status"] == "completed"
    assert status_response.json()["row_count"] == 1
    assert json.loads(download.content)[0]["action"] == "invoice.sent"


def test_export_requires_scope_and_hides_unknown_jobs() -> None:
    with TestClient(app) as client:
        secret = provision_export_key(client)
        headers = {"X-API-Key": secret}
        missing = client.get(f"/api/v1/exports/{uuid4()}", headers=headers)

    assert missing.status_code == 404
