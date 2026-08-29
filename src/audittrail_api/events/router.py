"""Audit-event ingestion and search endpoints."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Response, status
from sqlalchemy import select

from audittrail_api.api.dependencies import Session
from audittrail_api.auth.dependencies import APIKeyAccess, require_scope
from audittrail_api.events.models import AuditEvent
from audittrail_api.events.schemas import EventCreate, EventPage, EventRead
from audittrail_api.events.service import ingest_event

router = APIRouter(prefix="/events", tags=["events"])


@router.post("", response_model=EventRead, status_code=status.HTTP_201_CREATED)
async def create_event(
    payload: EventCreate,
    response: Response,
    session: Session,
    principal: APIKeyAccess,
) -> EventRead:
    require_scope(principal, "events:write")
    result = await ingest_event(session, principal, payload)
    if not result.created:
        response.status_code = status.HTTP_200_OK
    return EventRead.from_event(result.event)


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
