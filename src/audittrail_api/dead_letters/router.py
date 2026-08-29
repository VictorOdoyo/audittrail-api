"""Administrative dead-letter inspection and replay endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from audittrail_api.api.dependencies import AdminAccess, Session
from audittrail_api.database.mixins import utc_now
from audittrail_api.dead_letters.models import DeadLetterRecord
from audittrail_api.dead_letters.schemas import DeadLetterRead, DeadLetterRetry
from audittrail_api.workers.celery_app import celery_app

router = APIRouter(prefix="/dead-letters", tags=["dead letters"])
REPLAYABLE_TASKS = {
    "audittrail.generate_export",
    "audittrail.execute_retention",
}


@router.get("", response_model=list[DeadLetterRead])
async def list_dead_letters(
    session: Session,
    _: AdminAccess,
    record_status: Annotated[str | None, Query(alias="status")] = None,
    task_name: str | None = None,
) -> list[DeadLetterRecord]:
    statement = select(DeadLetterRecord).order_by(DeadLetterRecord.created_at.desc())
    if record_status:
        statement = statement.where(DeadLetterRecord.status == record_status)
    if task_name:
        statement = statement.where(DeadLetterRecord.task_name == task_name)
    return list(await session.scalars(statement))


@router.post("/{record_id}/retry", response_model=DeadLetterRetry)
async def retry_dead_letter(
    record_id: UUID,
    session: Session,
    _: AdminAccess,
) -> DeadLetterRetry:
    record = await session.get(DeadLetterRecord, record_id)
    if record is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Dead-letter record was not found.")
    if record.status != "pending":
        raise HTTPException(status.HTTP_409_CONFLICT, "Dead-letter record was already retried.")
    if record.task_name not in REPLAYABLE_TASKS:
        raise HTTPException(status.HTTP_409_CONFLICT, "Task type cannot be replayed safely.")

    replay = celery_app.send_task(
        record.task_name,
        args=record.payload.get("args", []),
        kwargs=record.payload.get("kwargs", {}),
    )
    record.status = "retried"
    record.last_retried_at = utc_now()
    await session.commit()
    return DeadLetterRetry(accepted=True, replacement_task_id=replay.id)
