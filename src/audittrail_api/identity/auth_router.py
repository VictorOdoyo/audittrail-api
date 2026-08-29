"""Human login endpoint."""

from fastapi import APIRouter, HTTPException, status

from audittrail_api.api.dependencies import RuntimeSettings, Session
from audittrail_api.identity.schemas import AccessToken, LoginRequest
from audittrail_api.identity.service import authenticate_user
from audittrail_api.identity.tokens import create_access_token

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/token", response_model=AccessToken)
async def login(
    payload: LoginRequest,
    session: Session,
    settings: RuntimeSettings,
) -> AccessToken:
    user = await authenticate_user(session, str(payload.email), payload.password)
    if user is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Email or password is incorrect.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(
        user.id,
        settings.jwt_secret,
        settings.jwt_issuer,
        settings.jwt_access_minutes,
    )
    return AccessToken(access_token=token, expires_in=settings.jwt_access_minutes * 60)
