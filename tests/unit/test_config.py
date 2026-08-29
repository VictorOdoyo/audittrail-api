import pytest
from pydantic import ValidationError

from audittrail_api.config import Settings


def test_settings_have_local_defaults() -> None:
    settings = Settings(_env_file=None)

    assert settings.environment == "development"
    assert settings.database_url.startswith("sqlite+")
    assert len(settings.api_key_pepper) >= 16


def test_production_rejects_development_secrets() -> None:
    with pytest.raises(ValidationError, match="explicitly configured secrets"):
        Settings(environment="production", auto_create_schema=False, _env_file=None)


def test_production_requires_migrations() -> None:
    with pytest.raises(ValidationError, match="Alembic migrations"):
        Settings(
            environment="production",
            admin_token="a-production-management-secret",  # noqa: S106
            api_key_pepper="a-production-api-key-pepper",
            auto_create_schema=True,
            _env_file=None,
        )
