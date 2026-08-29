"""Ingestion API-key authentication."""

from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, Response, status
from sqlalchemy import select

from audittrail_api.api.dependencies import RuntimeSettings, Session
from audittrail_api.auth.models import APIKey
from audittrail_api.auth.rate_limit import ScriptRedis, consume_rate_limit
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


async def enforce_ingestion_rate_limit(
    request: Request,
    response: Response,
    settings: RuntimeSettings,
    principal: APIKeyAccess,
) -> None:
    """Apply the configured ingestion allowance to one authenticated key."""

    if not settings.rate_limit_enabled:
        return
    redis: ScriptRedis = request.app.state.redis
    result = await consume_rate_limit(
        redis,
        identifier=str(principal.key_id),
        limit=settings.rate_limit_requests,
        window_seconds=settings.rate_limit_window_seconds,
    )
    response.headers["X-RateLimit-Remaining"] = str(result.remaining)
    if not result.allowed:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "The ingestion rate limit was exceeded.",
            headers={"Retry-After": str(result.retry_after)},
        )


RateLimitAccess = Annotated[None, Depends(enforce_ingestion_rate_limit)]
