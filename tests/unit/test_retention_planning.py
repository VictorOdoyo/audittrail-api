from datetime import UTC, datetime, timedelta
from uuid import uuid4

from audittrail_api.events.models import AuditEvent
from audittrail_api.retention.service import contiguous_expired_prefix


def event_at(occurred_at: datetime) -> AuditEvent:
    return AuditEvent(
        organization_id=uuid4(),
        application_id=uuid4(),
        external_id=uuid4(),
        occurred_at=occurred_at,
        actor_type="service",
        actor_id="source",
        action="record.viewed",
        resource_type="record",
        resource_id="record-1",
        event_metadata={},
        content_hash="a" * 64,
        event_hash="b" * 64,
    )


def test_retention_selects_only_contiguous_expired_prefix() -> None:
    cutoff = datetime(2026, 8, 1, tzinfo=UTC)
    events = [
        event_at(cutoff - timedelta(days=2)),
        event_at(cutoff + timedelta(days=1)),
        event_at(cutoff - timedelta(days=1)),
    ]

    selected = contiguous_expired_prefix(events, cutoff)

    assert selected == events[:1]


def test_retention_accepts_naive_sqlite_timestamps() -> None:
    cutoff = datetime(2026, 8, 1, tzinfo=UTC)

    selected = contiguous_expired_prefix([event_at(datetime(2026, 7, 1))], cutoff)

    assert len(selected) == 1
