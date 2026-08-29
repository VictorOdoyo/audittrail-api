"""Celery signals that durably capture terminal worker failures."""

import asyncio
from typing import Any

from celery.signals import task_failure

from audittrail_api.database.session import session_factory
from audittrail_api.dead_letters.service import record_terminal_failure


async def _persist_failure(
    task_name: str,
    task_id: str,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    exception: BaseException,
) -> None:
    async with session_factory() as session:
        await record_terminal_failure(
            session,
            task_name=task_name,
            task_id=task_id,
            args=args,
            kwargs=kwargs,
            exception=exception,
        )


@task_failure.connect  # type: ignore[untyped-decorator]
def persist_terminal_failure(
    sender: Any = None,
    task_id: str | None = None,
    exception: BaseException | None = None,
    args: tuple[Any, ...] | None = None,
    kwargs: dict[str, Any] | None = None,
    **_: Any,
) -> None:
    """Persist a failed task after Celery exhausts its configured retries."""

    if sender is None or task_id is None or exception is None:
        return
    asyncio.run(
        _persist_failure(
            sender.name,
            task_id,
            args or (),
            kwargs or {},
            exception,
        )
    )
