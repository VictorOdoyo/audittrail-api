"""API-key management contracts."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

APIKeyScope = Literal["events:write", "events:read", "exports:write"]


class APIKeyCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    scopes: list[APIKeyScope] = Field(min_length=1)

    @field_validator("scopes")
    @classmethod
    def deduplicate_scopes(cls, value: list[APIKeyScope]) -> list[APIKeyScope]:
        return list(dict.fromkeys(value))


class APIKeyIssued(BaseModel):
    id: UUID
    name: str
    prefix: str
    scopes: list[str]
    secret: str
    created_at: datetime


class APIKeyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    prefix: str
    scopes: list[str]
    created_at: datetime
    last_used_at: datetime | None
    revoked_at: datetime | None
