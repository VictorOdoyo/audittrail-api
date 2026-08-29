from uuid import uuid4

from fastapi.testclient import TestClient

from audittrail_api.main import app

ADMIN_HEADERS = {"Authorization": "Bearer local-admin-token"}


def test_management_can_bootstrap_one_membership() -> None:
    suffix = uuid4().hex[:8]
    with TestClient(app) as client:
        organization = client.post(
            "/api/v1/organizations",
            headers=ADMIN_HEADERS,
            json={"name": "RBAC Tenant", "slug": f"rbac-{suffix}"},
        ).json()
        user = client.post(
            "/api/v1/users",
            headers=ADMIN_HEADERS,
            json={
                "email": f"owner-{suffix}@example.com",
                "display_name": "Tenant Owner",
                "password": "correct horse battery staple",
            },
        ).json()
        payload = {"user_id": user["id"], "role": "owner"}
        created = client.post(
            f"/api/v1/organizations/{organization['id']}/members",
            headers=ADMIN_HEADERS,
            json=payload,
        )
        duplicate = client.post(
            f"/api/v1/organizations/{organization['id']}/members",
            headers=ADMIN_HEADERS,
            json=payload,
        )

    assert created.status_code == 201
    assert created.json()["role"] == "owner"
    assert duplicate.status_code == 409
