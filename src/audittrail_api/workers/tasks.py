"""Background export tasks with bounded retries."""

import asyncio
from uuid import UUID

from audittrail_api.config import get_settings
from audittrail_api.database.session import session_factory
from audittrail_api.exports.models import ExportJob
from audittrail_api.exports.service import generate_export
from audittrail_api.workers.celery_app import celery_app


async def _generate_export(job_id: UUID) -> None:
    async with session_factory() as session:
        job = await session.get(ExportJob, job_id)
        if job is None or job.status == "completed":
            return
        await generate_export(session, job, get_settings().export_directory)


@celery_app.task(  # type: ignore[untyped-decorator]
    name="audittrail.generate_export",
    autoretry_for=(RuntimeError,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def generate_export_task(job_id: str) -> None:
    """Bridge Celery's synchronous task interface to the async domain service."""

    asyncio.run(_generate_export(UUID(job_id)))
