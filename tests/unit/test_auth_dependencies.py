from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from audittrail_api.auth.dependencies import get_api_key_principal
from audittrail_api.auth.models import APIKey
from audittrail_api.auth.security import derive_digest
from audittrail_api.config import Settings


@pytest.mark.asyncio
async def test_api_key_dependency_returns_scoped_principal_and_updates_usage() -> None:
    settings = Settings(_env_file=None)
    raw_key = "at_live_a_valid_test_credential"
    key = APIKey(
        id=uuid4(),
        organization_id=uuid4(),
        application_id=uuid4(),
        name="Test writer",
        prefix=raw_key[:15],
        secret_digest=derive_digest(raw_key, settings.api_key_pepper),
        scopes=["events:read", "events:write"],
        revoked_at=None,
    )
    session = AsyncMock()
    session.scalar.return_value = key

    principal = await get_api_key_principal(session, settings, raw_key)

    assert principal.key_id == key.id
    assert principal.organization_id == key.organization_id
    assert principal.scopes == frozenset(key.scopes)
    assert key.last_used_at is not None
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_api_key_dependency_rejects_unknown_credentials() -> None:
    session = AsyncMock()
    session.scalar.return_value = None

    with pytest.raises(HTTPException) as error:
        await get_api_key_principal(
            session,
            Settings(_env_file=None),
            "at_live_an_unknown_credential",
        )

    assert error.value.status_code == 401
