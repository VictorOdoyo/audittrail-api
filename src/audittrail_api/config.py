"""Application configuration loaded from environment variables."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings with safe local-development defaults."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="AUDITTRAIL_",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "AuditTrail API"
    environment: Literal["development", "test", "production"] = "development"
    database_url: str = "sqlite+aiosqlite:///./audittrail.db"
    admin_token: str = Field(default="local-admin-token", min_length=12)
    api_key_pepper: str = Field(default="local-api-key-pepper", min_length=16)
    allowed_origins: list[str] = Field(default_factory=list)
    auto_create_schema: bool = True
    export_directory: Path = Path("exports")
    redis_url: str = "redis://localhost:6379/0"
    export_dispatch_mode: Literal["inline", "celery"] = "inline"
    retention_dispatch_mode: Literal["inline", "celery"] = "inline"
    rate_limit_enabled: bool = False
    rate_limit_requests: int = Field(default=120, ge=1, le=100_000)
    rate_limit_window_seconds: int = Field(default=60, ge=1, le=3600)
    jwt_secret: str = Field(default="local-jwt-signing-secret-change-me", min_length=32)
    jwt_issuer: str = "audittrail-api"
    jwt_access_minutes: int = Field(default=15, ge=1, le=1440)

    @model_validator(mode="after")
    def reject_unsafe_production_defaults(self) -> "Settings":
        if self.environment != "production":
            return self
        unsafe_values = {
            "local-admin-token",
            "local-api-key-pepper",
            "local-jwt-signing-secret-change-me",
        }
        if self.admin_token in unsafe_values or self.api_key_pepper in unsafe_values:
            raise ValueError("Production requires explicitly configured secrets.")
        if self.auto_create_schema:
            raise ValueError("Production schema changes must run through Alembic migrations.")
        return self


@lru_cache
def get_settings() -> Settings:
    """Return one configuration object per process."""

    return Settings()
