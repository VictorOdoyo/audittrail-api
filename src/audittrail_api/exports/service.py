"""Non-blocking export file generation."""

import asyncio
import csv
import json
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from audittrail_api.events.models import AuditEvent
from audittrail_api.events.schemas import EventRead
from audittrail_api.exports.models import ExportJob


def _write_json(path: Path, rows: Sequence[dict[str, Any]]) -> None:
    path.write_text(json.dumps(rows, indent=2, ensure_ascii=True), encoding="utf-8")


def _write_csv(path: Path, rows: Sequence[dict[str, Any]]) -> None:
    fieldnames = [
        "id",
        "external_id",
        "occurred_at",
        "actor_type",
        "actor_id",
        "action",
        "resource_type",
        "resource_id",
        "correlation_id",
        "metadata",
        "event_hash",
    ]
    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            normalized = dict(row)
            normalized["metadata"] = json.dumps(normalized["metadata"], sort_keys=True)
            writer.writerow(normalized)


async def generate_export(
    session: AsyncSession,
    job: ExportJob,
    export_directory: Path,
) -> ExportJob:
    """Generate one export while keeping filesystem I/O off the event loop."""

    job.status = "processing"
    await session.commit()
    query = select(AuditEvent).where(AuditEvent.application_id == job.application_id)
    if action := job.filters.get("action"):
        query = query.where(AuditEvent.action == action)
    if actor_id := job.filters.get("actor_id"):
        query = query.where(AuditEvent.actor_id == actor_id)
    if occurred_after := job.filters.get("occurred_after"):
        query = query.where(AuditEvent.occurred_at >= datetime.fromisoformat(occurred_after))
    if occurred_before := job.filters.get("occurred_before"):
        query = query.where(AuditEvent.occurred_at <= datetime.fromisoformat(occurred_before))
    events = list(await session.scalars(query.order_by(AuditEvent.occurred_at, AuditEvent.id)))
    rows = [EventRead.from_event(event).model_dump(mode="json") for event in events]
    await asyncio.to_thread(export_directory.mkdir, parents=True, exist_ok=True)
    path = export_directory / f"{job.id}.{job.format}"
    writer = _write_json if job.format == "json" else _write_csv
    try:
        await asyncio.to_thread(writer, path, rows)
    except OSError as exc:
        job.status = "failed"
        job.error_message = "The export file could not be written."
        await session.commit()
        raise RuntimeError(job.error_message) from exc
    job.status = "completed"
    job.row_count = len(rows)
    job.file_path = str(path)
    await session.commit()
    await session.refresh(job)
    return job
