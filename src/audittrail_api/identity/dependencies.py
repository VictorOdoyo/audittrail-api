"""JWT authentication and organization authorization dependencies."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from audittrail_api.api.dependencies import RuntimeSettings, Session
from audittrail_api.identity.models import User
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
