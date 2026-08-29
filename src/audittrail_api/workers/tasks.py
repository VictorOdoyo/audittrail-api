"""Background export tasks with bounded retries."""

import asyncio
from uuid import UUID

from audittrail_api.config import get_settings
from audittrail_api.database.session import session_factory
from audittrail_api.exports.models import ExportJob
from audittrail_api.exports.service import generate_export
from audittrail_api.retention.service import execute_retention
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


async def _execute_retention(organization_id: UUID) -> None:
    async with session_factory() as session:
        await execute_retention(session, organization_id)


@celery_app.task(  # type: ignore[untyped-decorator]
    name="audittrail.execute_retention",
    autoretry_for=(RuntimeError,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def execute_retention_task(organization_id: str) -> None:
    asyncio.run(_execute_retention(UUID(organization_id)))
