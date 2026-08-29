from fastapi.testclient import TestClient

from audittrail_api.main import app


def test_dead_letter_collection_requires_management_access() -> None:
    with TestClient(app) as client:
        unauthorized = client.get("/api/v1/dead-letters")
        authorized = client.get(
            "/api/v1/dead-letters",
            headers={"Authorization": "Bearer local-admin-token"},
        )

    assert unauthorized.status_code == 401
    assert authorized.status_code == 200
    assert isinstance(authorized.json(), list)
