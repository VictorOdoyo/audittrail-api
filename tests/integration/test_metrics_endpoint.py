from fastapi.testclient import TestClient

from audittrail_api.main import app


def test_metrics_endpoint_requires_management_token() -> None:
    with TestClient(app) as client:
        unauthorized = client.get("/metrics")
        response = client.get(
            "/metrics",
            headers={"Authorization": "Bearer local-admin-token"},
        )

    assert unauthorized.status_code == 401
    assert response.status_code == 200
    assert "audittrail_http_requests_total" in response.text
    assert response.headers["content-type"].startswith("text/plain")
