"""Transactional audit-event workflows."""

from dataclasses import dataclass

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from audittrail_api.auth.security import APIKeyPrincipal
from audittrail_api.events.integrity import chained_digest, content_digest
from audittrail_api.events.models import AuditEvent
from audittrail_api.events.schemas import EventCreate
from audittrail_api.organizations.models import Application


@dataclass(frozen=True, slots=True)
class IngestionResult:
    event: AuditEvent
    created: bool


async def ingest_event(
    session: AsyncSession,
    principal: APIKeyPrincipal,
    payload: EventCreate,
) -> IngestionResult:
    """Store one event exactly once and extend its application's hash chain."""

    payload_hash = content_digest(payload)
    existing = await session.scalar(
        select(AuditEvent).where(
            AuditEvent.application_id == principal.application_id,
            AuditEvent.external_id == payload.event_id,
        )
    )
    if existing is not None:
        if existing.content_hash != payload_hash:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "The event ID was already used with different content.",
            )
        return IngestionResult(event=existing, created=False)

    # Lock the source application so concurrent writers cannot fork the hash chain.
    await session.scalar(
        select(Application).where(Application.id == principal.application_id).with_for_update()
    )
    latest = await session.scalar(
        select(AuditEvent)
        .where(AuditEvent.application_id == principal.application_id)
        .order_by(AuditEvent.received_at.desc(), AuditEvent.id.desc())
        .limit(1)
    )
    previous_hash = latest.event_hash if latest else None
    event = AuditEvent(
        organization_id=principal.organization_id,
        application_id=principal.application_id,
        external_id=payload.event_id,
        occurred_at=payload.occurred_at,
        actor_type=payload.actor_type,
        actor_id=payload.actor_id,
        action=payload.action,
        resource_type=payload.resource_type,
        resource_id=payload.resource_id,
        correlation_id=payload.correlation_id,
        event_metadata=payload.metadata,
        content_hash=payload_hash,
        previous_hash=previous_hash,
        event_hash=chained_digest(payload_hash, previous_hash),
    )
    session.add(event)
    await session.commit()
    await session.refresh(event)
    return IngestionResult(event=event, created=True)
