from fastapi.testclient import TestClient

from audittrail_api.main import app


def test_http_errors_use_problem_contract_and_request_id() -> None:
    with TestClient(app) as client:
        response = client.get(
            "/api/v1/organizations",
            headers={"X-Request-ID": "support-case-42"},
        )

    assert response.status_code == 401
    assert response.headers["X-Request-ID"] == "support-case-42"
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["request_id"] == "support-case-42"
    assert response.json()["detail"] == "A valid management token is required."


def test_validation_errors_include_safe_field_details() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/organizations",
            headers={"Authorization": "Bearer local-admin-token"},
            json={"name": "", "slug": "not valid"},
        )

    assert response.status_code == 422
    assert response.json()["title"] == "Validation failed"
    assert {error["location"] for error in response.json()["errors"]} == {
        "body.name",
        "body.slug",
    }


def test_invalid_request_id_is_replaced() -> None:
    with TestClient(app) as client:
        response = client.get("/health/live", headers={"X-Request-ID": "x" * 101})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] != "x" * 101
