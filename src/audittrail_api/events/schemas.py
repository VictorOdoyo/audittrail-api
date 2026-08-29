"""Audit-event ingestion and query contracts."""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EventCreate(BaseModel):
    event_id: UUID
    occurred_at: datetime
    actor_type: str = Field(min_length=1, max_length=60)
    actor_id: str = Field(min_length=1, max_length=160)
    action: str = Field(pattern=r"^[a-z][a-z0-9_.-]+$", max_length=160)
    resource_type: str = Field(min_length=1, max_length=100)
    resource_id: str = Field(min_length=1, max_length=200)
    correlation_id: str | None = Field(default=None, max_length=160)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("occurred_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("occurred_at must include a timezone offset.")
        return value.astimezone(UTC)


class EventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    external_id: UUID
    organization_id: UUID
    application_id: UUID
    occurred_at: datetime
    received_at: datetime
    actor_type: str
    actor_id: str
    action: str
    resource_type: str
    resource_id: str
    correlation_id: str | None
    metadata: dict[str, Any]
    previous_hash: str | None
    event_hash: str

    @classmethod
    def from_event(cls, event: "AuditEvent") -> "EventRead":
        return cls(
            id=event.id,
            external_id=event.external_id,
            organization_id=event.organization_id,
            application_id=event.application_id,
            occurred_at=event.occurred_at,
            received_at=event.received_at,
            actor_type=event.actor_type,
            actor_id=event.actor_id,
            action=event.action,
            resource_type=event.resource_type,
            resource_id=event.resource_id,
            correlation_id=event.correlation_id,
            metadata=event.event_metadata,
            previous_hash=event.previous_hash,
            event_hash=event.event_hash,
        )


from audittrail_api.events.models import AuditEvent  # noqa: E402


class EventPage(BaseModel):
    items: list[EventRead]
    next_cursor: UUID | None


class BatchEventCreate(BaseModel):
    events: list[EventCreate] = Field(min_length=1, max_length=100)


class BatchEventResult(BaseModel):
    event_id: UUID
    status: str
    stored_id: UUID | None = None
    detail: str | None = None


class BatchIngestionResponse(BaseModel):
    accepted: int
    duplicates: int
    rejected: int
    results: list[BatchEventResult]


class ChainVerificationResponse(BaseModel):
    valid: bool
    event_count: int
    head_hash: str | None
