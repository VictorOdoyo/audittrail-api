"""Audit export request and status contracts."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ExportFilters(BaseModel):
    action: str | None = None
    actor_id: str | None = None
    occurred_after: datetime | None = None
    occurred_before: datetime | None = None


class ExportCreate(BaseModel):
    format: Literal["json", "csv"]
    filters: ExportFilters = ExportFilters()


class ExportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    application_id: UUID
    format: str
    status: str
    filters: dict[str, object]
    row_count: int | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime
