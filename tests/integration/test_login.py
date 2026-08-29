from uuid import uuid4

from fastapi.testclient import TestClient

from audittrail_api.identity.tokens import decode_access_token
from audittrail_api.main import app

ADMIN_HEADERS = {"Authorization": "Bearer local-admin-token"}
PASSWORD = "correct horse battery staple"  # noqa: S105


def test_user_can_exchange_password_for_access_token() -> None:
    email = f"login-{uuid4().hex[:8]}@example.com"
    with TestClient(app) as client:
        user = client.post(
            "/api/v1/users",
            headers=ADMIN_HEADERS,
            json={"email": email, "display_name": "Login User", "password": PASSWORD},
        ).json()
        response = client.post(
            "/api/v1/auth/token",
            json={"email": email, "password": PASSWORD},
        )

    assert response.status_code == 200
    claims = decode_access_token(
        response.json()["access_token"],
        "local-jwt-signing-secret-change-me",
        "audittrail-api",
    )
    assert str(claims.user_id) == user["id"]

    with TestClient(app) as client:
        identity = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {response.json()['access_token']}"},
        )
    assert identity.status_code == 200
    assert identity.json()["id"] == user["id"]


def test_login_rejects_wrong_and_unknown_credentials() -> None:
    with TestClient(app) as client:
        unknown = client.post(
            "/api/v1/auth/token",
            json={"email": "unknown@example.com", "password": "an unknown password"},
        )

    assert unknown.status_code == 401
    assert unknown.json()["detail"] == "Email or password is incorrect."


def test_current_identity_rejects_invalid_token() -> None:
    with TestClient(app) as client:
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid-token"},
        )

    assert response.status_code == 401
