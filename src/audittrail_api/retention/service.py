"""Retention planning that preserves hash-chain continuity."""

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from audittrail_api.events.models import AuditEvent
from audittrail_api.organizations.models import Application


@dataclass(frozen=True, slots=True)
class ApplicationRetentionPlan:
    application_id: UUID
    event_ids: tuple[UUID, ...]
    anchor_hash: str | None
    removed_through_at: datetime | None


def contiguous_expired_prefix(
    events: list[AuditEvent],
    cutoff_at: datetime,
) -> list[AuditEvent]:
    """Select only an expired prefix so retained chain links never have gaps."""

    expired: list[AuditEvent] = []
    for event in events:
        occurred_at = event.occurred_at
        if occurred_at.tzinfo is None:
            occurred_at = occurred_at.replace(tzinfo=UTC)
        if occurred_at >= cutoff_at:
            break
        expired.append(event)
    return expired


async def build_retention_plan(
    session: AsyncSession,
    organization_id: UUID,
    cutoff_at: datetime,
) -> list[ApplicationRetentionPlan]:
    applications = list(
        await session.scalars(
            select(Application).where(Application.organization_id == organization_id)
        )
    )
    plans: list[ApplicationRetentionPlan] = []
    for application in applications:
        events = list(
            await session.scalars(
                select(AuditEvent)
                .where(AuditEvent.application_id == application.id)
                .order_by(AuditEvent.received_at, AuditEvent.id)
            )
        )
        expired = contiguous_expired_prefix(events, cutoff_at)
        plans.append(
            ApplicationRetentionPlan(
                application_id=application.id,
                event_ids=tuple(event.id for event in expired),
                anchor_hash=expired[-1].event_hash if expired else None,
                removed_through_at=expired[-1].occurred_at if expired else None,
            )
        )
    return plans
