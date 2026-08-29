"""JWT authentication and organization authorization dependencies."""

from collections.abc import Awaitable, Callable
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from audittrail_api.api.dependencies import RuntimeSettings, Session
from audittrail_api.identity.models import Membership, User
from audittrail_api.identity.tokens import TokenError, decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)
BearerCredentials = Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)]


async def get_current_user(
    credentials: BearerCredentials,
    session: Session,
    settings: RuntimeSettings,
) -> User:
    unauthorized = HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        "A valid user access token is required.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise unauthorized
    try:
        claims = decode_access_token(
            credentials.credentials, settings.jwt_secret, settings.jwt_issuer
        )
    except TokenError as exc:
        raise unauthorized from exc
    user = await session.get(User, claims.user_id)
    if user is None or not user.is_active:
        raise unauthorized
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_current_membership(
    organization_id: UUID,
    user: CurrentUser,
    session: Session,
) -> Membership:
    from sqlalchemy import select

    membership = await session.scalar(
        select(Membership).where(
            Membership.organization_id == organization_id,
            Membership.user_id == user.id,
        )
    )
    if membership is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Organization membership is required.")
    return membership


CurrentMembership = Annotated[Membership, Depends(get_current_membership)]


def require_roles(*allowed_roles: str) -> Callable[[CurrentMembership], Awaitable[Membership]]:
    """Create a dependency that admits only specified organization roles."""

    async def authorize(membership: CurrentMembership) -> Membership:
        if membership.role not in allowed_roles:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                "The current organization role cannot perform this action.",
            )
        return membership

    return authorize
