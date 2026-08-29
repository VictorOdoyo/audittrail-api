from unittest.mock import AsyncMock, MagicMock

import pytest

from audittrail_api.dead_letters.service import json_safe, record_terminal_failure


def test_json_safe_normalizes_nested_task_arguments() -> None:
    marker = object()

    assert json_safe({"items": (1, marker), 2: {"ready": True}}) == {
        "items": [1, str(marker)],
        "2": {"ready": True},
    }


@pytest.mark.asyncio
async def test_record_terminal_failure_updates_an_existing_record() -> None:
    record = MagicMock(attempts=2, status="retried")
    session = AsyncMock()
    session.scalar.return_value = record

    result = await record_terminal_failure(
        session,
        task_name="audittrail.generate_export",
        task_id="task-1",
        args=("export-1",),
        kwargs={},
        exception=RuntimeError("storage unavailable"),
    )

    assert result is record
    assert record.attempts == 3
    assert record.status == "pending"
    assert record.error_type == "RuntimeError"
    session.commit.assert_awaited_once()
    session.refresh.assert_awaited_once_with(record)
