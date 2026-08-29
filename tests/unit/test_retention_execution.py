from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest

from audittrail_api.retention.models import RetentionPolicy
from audittrail_api.retention.service import (
    ApplicationRetentionPlan,
    LegalHoldError,
    execute_retention,
)


def execution_session() -> AsyncMock:
    session = AsyncMock()
    session.add = Mock()
    return session


@pytest.mark.asyncio
async def test_execute_retention_deletes_planned_prefix_and_writes_checkpoint() -> None:
    organization_id = uuid4()
    application_id = uuid4()
    event_ids = (uuid4(), uuid4())
    policy = RetentionPolicy(
        organization_id=organization_id,
        retention_days=365,
        legal_hold=False,
        updated_by="operator",
    )
    session = execution_session()
    session.scalar.side_effect = [policy, None]
    plans = [
        ApplicationRetentionPlan(
            application_id=application_id,
            event_ids=event_ids,
            anchor_hash="a" * 64,
            removed_through_at=datetime.now(UTC),
        ),
        ApplicationRetentionPlan(
            application_id=uuid4(),
            event_ids=(),
            anchor_hash=None,
            removed_through_at=None,
        ),
    ]

    with patch(
        "audittrail_api.retention.service.build_retention_plan",
        new=AsyncMock(return_value=plans),
    ):
        run = await execute_retention(session, organization_id)

    assert run.status == "completed"
    assert run.candidate_count == 2
    assert run.deleted_count == 2
    assert run.checkpoint_hashes == {str(application_id): "a" * 64}
    assert session.add.call_count == 2
    session.execute.assert_awaited_once()
    session.commit.assert_awaited_once()
    session.refresh.assert_awaited_once_with(run)


@pytest.mark.asyncio
async def test_execute_retention_requires_policy_without_legal_hold() -> None:
    missing_session = execution_session()
    missing_session.scalar.return_value = None
    with pytest.raises(LookupError):
        await execute_retention(missing_session, uuid4())

    held_session = execution_session()
    held_session.scalar.return_value = RetentionPolicy(
        organization_id=uuid4(),
        retention_days=365,
        legal_hold=True,
        updated_by="operator",
    )
    with pytest.raises(LegalHoldError):
        await execute_retention(held_session, uuid4())
