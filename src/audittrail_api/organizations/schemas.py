"""Public contracts for organizations and applications."""

import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class NamedResourceCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    slug: str = Field(min_length=2, max_length=80)

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not SLUG_PATTERN.fullmatch(normalized):
            raise ValueError("Slug must use lowercase letters, numbers, and single hyphens.")
        return normalized


class OrganizationCreate(NamedResourceCreate):
    pass


class OrganizationRead(NamedResourceCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime


class ApplicationCreate(NamedResourceCreate):
    pass


class ApplicationRead(NamedResourceCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    created_at: datetime
