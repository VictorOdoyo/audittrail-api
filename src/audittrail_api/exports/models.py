"""Persisted audit export job model."""

from typing import Any
from uuid import UUID

from sqlalchemy import JSON, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from audittrail_api.database.base import Base
from audittrail_api.database.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class ExportJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "export_jobs"

    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    application_id: Mapped[UUID] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), index=True, nullable=False
    )
    requested_by_key_id: Mapped[UUID] = mapped_column(
        ForeignKey("api_keys.id", ondelete="RESTRICT"), nullable=False
    )
    format: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True, nullable=False)
    filters: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    row_count: Mapped[int | None] = mapped_column(Integer)
    file_path: Mapped[str | None] = mapped_column(String(500))
    error_message: Mapped[str | None] = mapped_column(Text)
