"""Retention governance contracts."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RetentionPolicyUpdate(BaseModel):
    retention_days: int = Field(ge=30, le=3650)
    legal_hold: bool = False
    updated_by: str = Field(min_length=2, max_length=160)


class RetentionPolicyRead(RetentionPolicyUpdate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    created_at: datetime
    updated_at: datetime


class ApplicationRetentionPreview(BaseModel):
    application_id: UUID
    candidate_count: int
    anchor_hash: str | None


class RetentionPreview(BaseModel):
    organization_id: UUID
    cutoff_at: datetime
    legal_hold: bool
    candidate_count: int
    applications: list[ApplicationRetentionPreview]


class RetentionDispatch(BaseModel):
    status: str
    run_id: UUID | None = None
