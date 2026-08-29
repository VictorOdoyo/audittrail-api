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


def test_owner_can_list_and_change_member_roles() -> None:
    suffix = uuid4().hex[:8]
    password = "correct horse battery staple"  # noqa: S105
    with TestClient(app) as client:
        organization = client.post(
            "/api/v1/organizations",
            headers=ADMIN_HEADERS,
            json={"name": "Role Tenant", "slug": f"roles-{suffix}"},
        ).json()
        users = []
        for label in ("owner", "writer"):
            users.append(
                client.post(
                    "/api/v1/users",
                    headers=ADMIN_HEADERS,
                    json={
                        "email": f"{label}-{suffix}@example.com",
                        "display_name": f"{label.title()} User",
                        "password": password,
                    },
                ).json()
            )
        owner_membership = client.post(
            f"/api/v1/organizations/{organization['id']}/members",
            headers=ADMIN_HEADERS,
            json={"user_id": users[0]["id"], "role": "owner"},
        ).json()
        writer_membership = client.post(
            f"/api/v1/organizations/{organization['id']}/members",
            headers=ADMIN_HEADERS,
            json={"user_id": users[1]["id"], "role": "writer"},
        ).json()
        owner_token = client.post(
            "/api/v1/auth/token",
            json={"email": users[0]["email"], "password": password},
        ).json()["access_token"]
        bearer = {"Authorization": f"Bearer {owner_token}"}
        listed = client.get(
            f"/api/v1/organizations/{organization['id']}/members",
            headers=bearer,
        )
        updated = client.patch(
            f"/api/v1/organizations/{organization['id']}/members/{writer_membership['id']}",
            headers=bearer,
            json={"role": "auditor"},
        )

    assert owner_membership["role"] == "owner"
    assert len(listed.json()) == 2
    assert updated.json()["role"] == "auditor"
