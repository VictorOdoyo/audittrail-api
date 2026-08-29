from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from audittrail_api.dead_letters.signals import _persist_failure, persist_terminal_failure


@pytest.mark.asyncio
async def test_failure_signal_writes_through_session_factory() -> None:
    session = AsyncMock()
    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=session)
    context.__aexit__ = AsyncMock(return_value=None)
    error = RuntimeError("worker failed")

    with (
        patch("audittrail_api.dead_letters.signals.session_factory", return_value=context),
        patch(
            "audittrail_api.dead_letters.signals.record_terminal_failure",
            new=AsyncMock(),
        ) as record,
    ):
        await _persist_failure("audittrail.generate_export", "task-3", ("job-1",), {}, error)

    record.assert_awaited_once_with(
        session,
        task_name="audittrail.generate_export",
        task_id="task-3",
        args=("job-1",),
        kwargs={},
        exception=error,
    )


def test_failure_signal_ignores_incomplete_and_dispatches_complete_events() -> None:
    sender = MagicMock(name="sender")
    sender.name = "audittrail.generate_export"

    with patch("audittrail_api.dead_letters.signals.asyncio.run") as run:
        persist_terminal_failure(sender=sender)
        run.assert_not_called()

        persist_terminal_failure(
            sender=sender,
            task_id="task-4",
            exception=RuntimeError("failed"),
            args=("job-2",),
            kwargs={},
        )

    run.assert_called_once()
    run.call_args.args[0].close()
