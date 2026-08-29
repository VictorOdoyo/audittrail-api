"""Persistence helpers for terminal background-task failures."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from audittrail_api.dead_letters.models import DeadLetterRecord


def json_safe(value: Any) -> Any:
    """Convert task arguments to values accepted by JSON database columns."""

    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, list | tuple | set):
        return [json_safe(item) for item in value]
    return str(value)


async def record_terminal_failure(
    session: AsyncSession,
    *,
    task_name: str,
    task_id: str,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    exception: BaseException,
) -> DeadLetterRecord:
    """Create or refresh the durable record for one failed task execution."""

    record = await session.scalar(
        select(DeadLetterRecord).where(DeadLetterRecord.task_id == task_id)
    )
    if record is None:
        record = DeadLetterRecord(
            task_name=task_name,
            task_id=task_id,
            payload={"args": json_safe(args), "kwargs": json_safe(kwargs)},
            error_type=type(exception).__name__,
            error_message=str(exception),
        )
        session.add(record)
    else:
        record.attempts += 1
        record.error_type = type(exception).__name__
        record.error_message = str(exception)
        record.status = "pending"
    await session.commit()
    await session.refresh(record)
    return record
