from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from audittrail_api.dead_letters.models import DeadLetterRecord
from audittrail_api.dead_letters.router import retry_dead_letter


@pytest.mark.asyncio
async def test_retry_dispatches_original_payload_once() -> None:
    record = DeadLetterRecord(
        task_name="audittrail.generate_export",
        task_id="failed-task",
        payload={"args": ["export-id"], "kwargs": {}},
        error_type="RuntimeError",
        error_message="storage offline",
        status="pending",
    )
    session = AsyncMock()
    session.get.return_value = record
    replacement = MagicMock(id="replacement-task")

    with patch(
        "audittrail_api.dead_letters.router.celery_app.send_task",
        return_value=replacement,
    ) as send_task:
        result = await retry_dead_letter(uuid4(), session, None)

    assert result.replacement_task_id == "replacement-task"
    assert record.status == "retried"
    assert record.last_retried_at is not None
    send_task.assert_called_once_with(
        "audittrail.generate_export",
        args=["export-id"],
        kwargs={},
    )
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_retry_rejects_an_already_retried_record() -> None:
    record = MagicMock(status="retried")
    session = AsyncMock()
    session.get.return_value = record

    with pytest.raises(HTTPException) as error:
        await retry_dead_letter(uuid4(), session, None)

    assert error.value.status_code == 409


@pytest.mark.asyncio
async def test_retry_rejects_unknown_task_types_without_dispatching() -> None:
    record = MagicMock(status="pending", task_name="third.party.unsafe_task")
    session = AsyncMock()
    session.get.return_value = record

    with (
        patch("audittrail_api.dead_letters.router.celery_app.send_task") as send_task,
        pytest.raises(HTTPException) as error,
    ):
        await retry_dead_letter(uuid4(), session, None)

    assert error.value.status_code == 409
    send_task.assert_not_called()
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_retry_returns_not_found_for_missing_record() -> None:
    session = AsyncMock()
    session.get.return_value = None

    with pytest.raises(HTTPException) as error:
        await retry_dead_letter(uuid4(), session, None)

    assert error.value.status_code == 404
