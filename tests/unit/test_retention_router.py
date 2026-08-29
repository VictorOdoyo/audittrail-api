from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from audittrail_api.organizations.models import Organization
from audittrail_api.retention.models import RetentionPolicy
from audittrail_api.retention.router import get_retention_policy, update_retention_policy
from audittrail_api.retention.schemas import RetentionPolicyUpdate


def session_mock() -> AsyncMock:
    session = AsyncMock()
    session.add = Mock()
    return session


@pytest.mark.asyncio
async def test_policy_creation_branch() -> None:
    organization_id = uuid4()
    session = session_mock()
    session.get.return_value = Organization(id=organization_id, name="Tenant", slug="tenant")
    session.scalar.return_value = None
    payload = RetentionPolicyUpdate(
        retention_days=365,
        legal_hold=False,
        updated_by="admin-1",
    )

    policy = await update_retention_policy(organization_id, payload, session, None)

    assert policy.organization_id == organization_id
    assert policy.retention_days == 365
    session.add.assert_called_once_with(policy)
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_policy_update_and_read_branches() -> None:
    organization_id = uuid4()
    policy = RetentionPolicy(
        organization_id=organization_id,
        retention_days=365,
        legal_hold=False,
        updated_by="admin-1",
    )
    session = session_mock()
    session.get.return_value = Organization(id=organization_id, name="Tenant", slug="tenant")
    session.scalar.return_value = policy
    payload = RetentionPolicyUpdate(
        retention_days=730,
        legal_hold=True,
        updated_by="auditor-2",
    )

    updated = await update_retention_policy(organization_id, payload, session, None)
    fetched = await get_retention_policy(organization_id, session, None)

    assert updated.retention_days == 730
    assert updated.legal_hold is True
    assert fetched is policy


@pytest.mark.asyncio
async def test_missing_policy_raises_not_found() -> None:
    session = session_mock()
    session.scalar.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await get_retention_policy(uuid4(), session, None)

    assert exc_info.value.status_code == 404
