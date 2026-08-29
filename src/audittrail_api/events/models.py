"""Immutable audit-event persistence model."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import JSON, DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from audittrail_api.database.base import Base
from audittrail_api.database.mixins import UUIDPrimaryKeyMixin, utc_now


class AuditEvent(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "audit_events"
    __table_args__ = (
        UniqueConstraint("application_id", "external_id", name="uq_event_application_external"),
        Index("ix_events_org_occurred", "organization_id", "occurred_at"),
        Index("ix_events_app_action", "application_id", "action"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    application_id: Mapped[UUID] = mapped_column(
        ForeignKey("applications.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    external_id: Mapped[UUID] = mapped_column(nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, index=True, nullable=False
    )
    actor_type: Mapped[str] = mapped_column(String(60), nullable=False)
    actor_id: Mapped[str] = mapped_column(String(160), nullable=False)
    action: Mapped[str] = mapped_column(String(160), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(200), nullable=False)
    correlation_id: Mapped[str | None] = mapped_column(String(160), index=True)
    event_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    previous_hash: Mapped[str | None] = mapped_column(String(64))
    event_hash: Mapped[str] = mapped_column(String(64), nullable=False)
