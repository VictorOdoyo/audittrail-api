from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from audittrail_api.config import Settings
from audittrail_api.main import create_app


def test_rate_limit_mode_checks_and_closes_redis() -> None:
    redis = AsyncMock()
    settings = Settings(rate_limit_enabled=True, auto_create_schema=False, _env_file=None)
    with (
        patch("audittrail_api.main.Redis.from_url", return_value=redis) as from_url,
        TestClient(create_app(settings)) as client,
    ):
        response = client.get("/health/live")

    assert response.status_code == 200
    from_url.assert_called_once_with(settings.redis_url, decode_responses=True)
    redis.ping.assert_awaited_once()
    redis.aclose.assert_awaited_once()
