from audittrail_api.dead_letters.models import DeadLetterRecord


def test_dead_letter_captures_replayable_failure_context() -> None:
    record = DeadLetterRecord(
        task_name="audittrail.generate_export",
        task_id="task-42",
        payload={"args": ["export-id"], "kwargs": {}},
        error_type="RuntimeError",
        error_message="Storage unavailable",
        attempts=4,
        status="pending",
    )

    assert record.payload["args"] == ["export-id"]
    assert record.attempts == 4
