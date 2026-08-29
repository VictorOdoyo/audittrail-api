"""Audit-event ingestion and search endpoints."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import select

from audittrail_api.api.dependencies import Session
from audittrail_api.auth.dependencies import APIKeyAccess, RateLimitAccess, require_scope
from audittrail_api.events.integrity import verify_chain
from audittrail_api.events.models import AuditEvent
from audittrail_api.events.schemas import (
    BatchEventCreate,
    BatchEventResult,
    BatchIngestionResponse,
    ChainVerificationResponse,
    EventCreate,
    EventPage,
    EventRead,
)
from audittrail_api.events.service import ingest_event

router = APIRouter(prefix="/events", tags=["events"])


@router.post("", response_model=EventRead, status_code=status.HTTP_201_CREATED)
async def create_event(
    payload: EventCreate,
    response: Response,
    session: Session,
    principal: APIKeyAccess,
    _: RateLimitAccess,
) -> EventRead:
    require_scope(principal, "events:write")
    result = await ingest_event(session, principal, payload)
    if not result.created:
        response.status_code = status.HTTP_200_OK
    return EventRead.from_event(result.event)


@router.post("/batch", response_model=BatchIngestionResponse)
async def create_event_batch(
    payload: BatchEventCreate,
    session: Session,
    principal: APIKeyAccess,
    _: RateLimitAccess,
) -> BatchIngestionResponse:
    """Ingest a bounded batch and report each item's outcome independently."""

    require_scope(principal, "events:write")
    results: list[BatchEventResult] = []
    for item in payload.events:
        try:
            outcome = await ingest_event(session, principal, item)
            results.append(
                BatchEventResult(
                    event_id=item.event_id,
                    stored_id=outcome.event.id,
                    status="accepted" if outcome.created else "duplicate",
                )
            )
        except HTTPException as exc:
            results.append(
                BatchEventResult(
                    event_id=item.event_id,
                    status="rejected",
                    detail=str(exc.detail),
                )
            )
    return BatchIngestionResponse(
        accepted=sum(item.status == "accepted" for item in results),
        duplicates=sum(item.status == "duplicate" for item in results),
        rejected=sum(item.status == "rejected" for item in results),
        results=results,
    )


@router.get("/verify-chain", response_model=ChainVerificationResponse)
async def check_event_chain(
    session: Session,
    principal: APIKeyAccess,
) -> ChainVerificationResponse:
    """Verify all events belonging to the authenticated source application."""

    require_scope(principal, "events:read")
    events = list(
        await session.scalars(
            select(AuditEvent)
            .where(AuditEvent.application_id == principal.application_id)
            .order_by(AuditEvent.received_at, AuditEvent.id)
        )
    )
    return ChainVerificationResponse(
        valid=verify_chain(events),
        event_count=len(events),
        head_hash=events[-1].event_hash if events else None,
    )


@router.get("/{event_id}", response_model=EventRead)
async def get_event(
    event_id: UUID,
    session: Session,
    principal: APIKeyAccess,
) -> EventRead:
    require_scope(principal, "events:read")
    event = await session.scalar(
        select(AuditEvent).where(
            AuditEvent.id == event_id,
            AuditEvent.application_id == principal.application_id,
        )
    )
    if event is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Event was not found.")
    return EventRead.from_event(event)


@router.get("", response_model=EventPage)
async def search_events(
    session: Session,
    principal: APIKeyAccess,
    action: str | None = None,
    actor_id: str | None = None,
    resource_type: str | None = None,
    correlation_id: str | None = None,
    occurred_after: datetime | None = None,
    occurred_before: datetime | None = None,
    cursor: UUID | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> EventPage:
    require_scope(principal, "events:read")
    query = select(AuditEvent).where(AuditEvent.application_id == principal.application_id)
    if action:
        query = query.where(AuditEvent.action == action)
    if actor_id:
        query = query.where(AuditEvent.actor_id == actor_id)
    if resource_type:
        query = query.where(AuditEvent.resource_type == resource_type)
    if correlation_id:
        query = query.where(AuditEvent.correlation_id == correlation_id)
    if occurred_after:
        query = query.where(AuditEvent.occurred_at >= occurred_after)
    if occurred_before:
        query = query.where(AuditEvent.occurred_at <= occurred_before)
    if cursor:
        query = query.where(AuditEvent.id > cursor)
    events = list(await session.scalars(query.order_by(AuditEvent.id).limit(limit + 1)))
    has_more = len(events) > limit
    page_items = events[:limit]
    return EventPage(
        items=[EventRead.from_event(event) for event in page_items],
        next_cursor=page_items[-1].id if has_more else None,
    )
