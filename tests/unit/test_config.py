from audittrail_api.config import Settings


def test_settings_have_local_defaults() -> None:
    settings = Settings(_env_file=None)

    assert settings.environment == "development"
    assert settings.database_url.startswith("sqlite+")
    assert len(settings.api_key_pepper) >= 16
