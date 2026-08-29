"""Shared authentication and database dependencies."""

from hmac import compare_digest
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from audittrail_api.config import Settings, get_settings
from audittrail_api.database.session import get_session

Session = Annotated[AsyncSession, Depends(get_session)]
RuntimeSettings = Annotated[Settings, Depends(get_settings)]


async def require_admin_token(
    settings: RuntimeSettings,
    authorization: Annotated[str | None, Header()] = None,
) -> None:
    """Protect management endpoints with a separate bootstrap credential."""

    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not compare_digest(token, settings.admin_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A valid management token is required.",
            headers={"WWW-Authenticate": "Bearer"},
        )


AdminAccess = Annotated[None, Depends(require_admin_token)]
