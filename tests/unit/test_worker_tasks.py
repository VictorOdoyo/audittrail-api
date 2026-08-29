from unittest.mock import AsyncMock, patch
from uuid import uuid4

from audittrail_api.workers.tasks import execute_retention_task, generate_export_task


def test_export_task_runs_async_worker_bridge() -> None:
    job_id = uuid4()
    with patch("audittrail_api.workers.tasks._generate_export", new=AsyncMock()) as generate:
        generate_export_task.run(str(job_id))

    generate.assert_awaited_once_with(job_id)


def test_retention_task_runs_async_worker_bridge() -> None:
    organization_id = uuid4()
    with patch("audittrail_api.workers.tasks._execute_retention", new=AsyncMock()) as execute:
        execute_retention_task.run(str(organization_id))

    execute.assert_awaited_once_with(organization_id)
