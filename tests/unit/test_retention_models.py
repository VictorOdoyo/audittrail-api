from datetime import UTC, datetime
from uuid import uuid4

from audittrail_api.retention.models import RetentionCheckpoint, RetentionRun


def test_retention_run_and_checkpoint_capture_integrity_state() -> None:
    application_id = uuid4()
    cutoff = datetime(2026, 1, 1, tzinfo=UTC)
    run = RetentionRun(organization_id=uuid4(), cutoff_at=cutoff)
    checkpoint = RetentionCheckpoint(
        application_id=application_id,
        anchor_hash="a" * 64,
        removed_through_at=cutoff,
        removed_event_count=4,
    )

    assert run.cutoff_at == cutoff
    assert checkpoint.application_id == application_id
    assert checkpoint.removed_event_count == 4
