"""Ingestion API-key authentication."""

from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select

from audittrail_api.api.dependencies import RuntimeSettings, Session
from audittrail_api.auth.models import APIKey
from audittrail_api.auth.security import APIKeyPrincipal, verify_api_key
from audittrail_api.database.mixins import utc_now


async def get_api_key_principal(
    session: Session,
    settings: RuntimeSettings,
    raw_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> APIKeyPrincipal:
    """Authenticate an active application credential."""

    if not raw_key or len(raw_key) < 15:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "A valid API key is required.")
    stored_key = await session.scalar(select(APIKey).where(APIKey.prefix == raw_key[:15]))
    if (
        stored_key is None
        or stored_key.revoked_at is not None
        or not verify_api_key(raw_key, stored_key.secret_digest, settings.api_key_pepper)
    ):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "A valid API key is required.")
    stored_key.last_used_at = utc_now()
    await session.commit()
    return APIKeyPrincipal(
        key_id=stored_key.id,
        organization_id=stored_key.organization_id,
        application_id=stored_key.application_id,
        scopes=frozenset(stored_key.scopes),
    )


APIKeyAccess = Annotated[APIKeyPrincipal, Depends(get_api_key_principal)]


def require_scope(principal: APIKeyPrincipal, scope: str) -> None:
    if scope not in principal.scopes:
        raise HTTPException(status.HTTP_403_FORBIDDEN, f"API key lacks the {scope} scope.")
