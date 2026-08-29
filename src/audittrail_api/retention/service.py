"""Retention planning that preserves hash-chain continuity."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from audittrail_api.events.models import AuditEvent
from audittrail_api.organizations.models import Application
from audittrail_api.retention.models import RetentionCheckpoint, RetentionPolicy, RetentionRun


class LegalHoldError(RuntimeError):
    pass


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


async def execute_retention(session: AsyncSession, organization_id: UUID) -> RetentionRun:
    """Delete eligible prefixes and retain a verification anchor for each application."""

    policy = await session.scalar(
        select(RetentionPolicy).where(RetentionPolicy.organization_id == organization_id)
    )
    if policy is None:
        raise LookupError("Retention policy was not found.")
    if policy.legal_hold:
        raise LegalHoldError("Retention cannot run while a legal hold is active.")
    cutoff_at = datetime.now(UTC) - timedelta(days=policy.retention_days)
    plans = await build_retention_plan(session, organization_id, cutoff_at)
    run = RetentionRun(
        organization_id=organization_id,
        cutoff_at=cutoff_at,
        status="processing",
        candidate_count=sum(len(plan.event_ids) for plan in plans),
        deleted_count=0,
        checkpoint_hashes={},
    )
    session.add(run)
    await session.flush()
    for plan in plans:
        if not plan.event_ids or not plan.anchor_hash or not plan.removed_through_at:
            continue
        checkpoint = await session.scalar(
            select(RetentionCheckpoint).where(
                RetentionCheckpoint.application_id == plan.application_id
            )
        )
        if checkpoint is None:
            checkpoint = RetentionCheckpoint(
                application_id=plan.application_id,
                anchor_hash=plan.anchor_hash,
                removed_through_at=plan.removed_through_at,
                removed_event_count=len(plan.event_ids),
            )
            session.add(checkpoint)
        else:
            checkpoint.anchor_hash = plan.anchor_hash
            checkpoint.removed_through_at = plan.removed_through_at
            checkpoint.removed_event_count += len(plan.event_ids)
        await session.execute(delete(AuditEvent).where(AuditEvent.id.in_(plan.event_ids)))
        run.deleted_count += len(plan.event_ids)
        run.checkpoint_hashes[str(plan.application_id)] = plan.anchor_hash
    run.status = "completed"
    await session.commit()
    await session.refresh(run)
    return run
