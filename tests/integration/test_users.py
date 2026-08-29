from uuid import uuid4

from fastapi.testclient import TestClient

from audittrail_api.main import app

ADMIN_HEADERS = {"Authorization": "Bearer local-admin-token"}


def test_user_can_be_provisioned_listed_and_not_duplicated() -> None:
    email = f"auditor-{uuid4().hex[:8]}@example.com"
    payload = {
        "email": email,
        "display_name": "Example Auditor",
        "password": "correct horse battery staple",
    }
    with TestClient(app) as client:
        created = client.post("/api/v1/users", headers=ADMIN_HEADERS, json=payload)
        duplicate = client.post("/api/v1/users", headers=ADMIN_HEADERS, json=payload)
        listed = client.get("/api/v1/users", headers=ADMIN_HEADERS)

    assert created.status_code == 201
    assert created.json()["email"] == email
    assert "password" not in created.json()
    assert duplicate.status_code == 409
    assert any(user["id"] == created.json()["id"] for user in listed.json())
