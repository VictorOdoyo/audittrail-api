"""Organization retention policy model."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from audittrail_api.database.base import Base
from audittrail_api.database.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class RetentionPolicy(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "retention_policies"

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    retention_days: Mapped[int] = mapped_column(Integer, default=365, nullable=False)
    legal_hold: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    updated_by: Mapped[str] = mapped_column(String(160), nullable=False)


class RetentionRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "retention_runs"

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    cutoff_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True, nullable=False)
    candidate_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    deleted_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    checkpoint_hashes: Mapped[dict[str, str]] = mapped_column(JSON, default=dict, nullable=False)
    error_message: Mapped[str | None] = mapped_column(String(500))


class RetentionCheckpoint(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "retention_checkpoints"

    application_id: Mapped[UUID] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), unique=True, index=True, nullable=False
    )
    anchor_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    removed_through_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    removed_event_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
