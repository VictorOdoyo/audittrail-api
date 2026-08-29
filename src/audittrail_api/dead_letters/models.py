"""Durable terminal worker failure records."""

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from audittrail_api.database.base import Base
from audittrail_api.database.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class DeadLetterRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "dead_letter_records"

    task_name: Mapped[str] = mapped_column(String(160), index=True, nullable=False)
    task_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    error_type: Mapped[str] = mapped_column(String(160), nullable=False)
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True, nullable=False)
    last_retried_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
