"""Scoped audit export endpoints."""

import asyncio
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import select

from audittrail_api.api.dependencies import RuntimeSettings, Session
from audittrail_api.auth.dependencies import APIKeyAccess, require_scope
from audittrail_api.exports.models import ExportJob
from audittrail_api.exports.schemas import ExportCreate, ExportRead
from audittrail_api.exports.service import generate_export
from audittrail_api.workers.tasks import generate_export_task

router = APIRouter(prefix="/exports", tags=["exports"])


async def owned_export(session: Session, job_id: UUID, application_id: UUID) -> ExportJob:
    job = await session.scalar(
        select(ExportJob).where(
            ExportJob.id == job_id,
            ExportJob.application_id == application_id,
        )
    )
    if job is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Export job was not found.")
    return job


@router.post("", response_model=ExportRead, status_code=status.HTTP_201_CREATED)
async def create_export(
    payload: ExportCreate,
    session: Session,
    settings: RuntimeSettings,
    principal: APIKeyAccess,
) -> ExportJob:
    require_scope(principal, "exports:write")
    job = ExportJob(
        organization_id=principal.organization_id,
        application_id=principal.application_id,
        requested_by_key_id=principal.key_id,
        format=payload.format,
        filters=payload.filters.model_dump(mode="json", exclude_none=True),
    )
    session.add(job)
    await session.commit()
    await session.refresh(job)
    if settings.export_dispatch_mode == "celery":
        generate_export_task.delay(str(job.id))
        return job
    return await generate_export(session, job, settings.export_directory)


@router.get("/{job_id}", response_model=ExportRead)
async def get_export(
    job_id: UUID,
    session: Session,
    principal: APIKeyAccess,
) -> ExportJob:
    require_scope(principal, "exports:write")
    return await owned_export(session, job_id, principal.application_id)


@router.get("/{job_id}/download", response_class=FileResponse)
async def download_export(
    job_id: UUID,
    session: Session,
    principal: APIKeyAccess,
) -> FileResponse:
    require_scope(principal, "exports:write")
    job = await owned_export(session, job_id, principal.application_id)
    if job.status != "completed" or not job.file_path:
        raise HTTPException(status.HTTP_409_CONFLICT, "Export file is not ready.")
    file_exists = await asyncio.to_thread(Path(job.file_path).is_file)
    if not file_exists:
        raise HTTPException(status.HTTP_409_CONFLICT, "Export file is not ready.")
    return FileResponse(
        job.file_path,
        filename=f"audit-events-{job.id}.{job.format}",
        media_type="application/json" if job.format == "json" else "text/csv",
    )
