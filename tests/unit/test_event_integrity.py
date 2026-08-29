from datetime import UTC, datetime
from uuid import UUID

from audittrail_api.events.integrity import chained_digest, content_digest
from audittrail_api.events.schemas import EventCreate


def event_payload() -> EventCreate:
    return EventCreate(
        event_id=UUID("169d0dc4-9c0d-44f5-9a23-34f4aa1583e0"),
        occurred_at=datetime(2026, 8, 29, 12, 0, tzinfo=UTC),
        actor_type="user",
        actor_id="user-42",
        action="invoice.approved",
        resource_type="invoice",
        resource_id="inv-100",
        metadata={"amount": 7500, "currency": "USD"},
    )


def test_content_digest_is_deterministic() -> None:
    first = event_payload()
    second = event_payload().model_copy(update={"metadata": {"currency": "USD", "amount": 7500}})

    assert content_digest(first) == content_digest(second)


def test_chain_digest_changes_with_previous_hash() -> None:
    digest = content_digest(event_payload())

    assert chained_digest(digest, None) != chained_digest(digest, "1" * 64)
