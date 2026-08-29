from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

from fastapi.testclient import TestClient

from audittrail_api.config import Settings, get_settings
from audittrail_api.main import app

ADMIN_HEADERS = {"Authorization": "Bearer local-admin-token"}


def provision_key(client: TestClient) -> str:
    suffix = uuid4().hex[:8]
    organization = client.post(
        "/api/v1/organizations",
        headers=ADMIN_HEADERS,
        json={"name": "Limited Tenant", "slug": f"limited-{suffix}"},
    ).json()
    application = client.post(
        f"/api/v1/organizations/{organization['id']}/applications",
        headers=ADMIN_HEADERS,
        json={"name": "Limited Source", "slug": "limited-source"},
    ).json()
    return str(
        client.post(
            f"/api/v1/applications/{application['id']}/api-keys",
            headers=ADMIN_HEADERS,
            json={"name": "Limited key", "scopes": ["events:write"]},
        ).json()["secret"]
    )


def test_ingestion_returns_retry_window_when_limit_is_exhausted() -> None:
    settings = Settings(
        rate_limit_enabled=True,
        rate_limit_requests=1,
        rate_limit_window_seconds=60,
        _env_file=None,
    )
    redis = AsyncMock()
    redis.eval.return_value = [2, 37]
    app.state.redis = redis
    app.dependency_overrides[get_settings] = lambda: settings
    try:
        with TestClient(app) as client:
            secret = provision_key(client)
            response = client.post(
                "/api/v1/events",
                headers={"X-API-Key": secret},
                json={
                    "event_id": str(uuid4()),
                    "occurred_at": datetime.now(UTC).isoformat(),
                    "actor_type": "service",
                    "actor_id": "limited-source",
                    "action": "record.created",
                    "resource_type": "record",
                    "resource_id": "record-1",
                    "metadata": {},
                },
            )
    finally:
        app.dependency_overrides.pop(get_settings, None)

    assert response.status_code == 429
    assert response.headers["Retry-After"] == "37"
    assert response.json()["detail"] == "The ingestion rate limit was exceeded."
