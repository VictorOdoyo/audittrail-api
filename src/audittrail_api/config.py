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

    @model_validator(mode="after")
    def reject_unsafe_production_defaults(self) -> "Settings":
        if self.environment != "production":
            return self
        unsafe_values = {"local-admin-token", "local-api-key-pepper"}
        if self.admin_token in unsafe_values or self.api_key_pepper in unsafe_values:
            raise ValueError("Production requires explicitly configured secrets.")
        if self.auto_create_schema:
            raise ValueError("Production schema changes must run through Alembic migrations.")
        return self


@lru_cache
def get_settings() -> Settings:
    """Return one configuration object per process."""

    return Settings()
