"""Dead-letter operational contracts."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DeadLetterRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    task_name: str
    task_id: str
    payload: dict[str, Any]
    error_type: str
    error_message: str
    attempts: int
    status: str
    created_at: datetime
    last_retried_at: datetime | None


class DeadLetterRetry(BaseModel):
    accepted: bool
    replacement_task_id: str
