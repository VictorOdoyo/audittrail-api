"""Short-lived JWT access tokens."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt


class TokenError(ValueError):
    """Raised when an access token cannot be trusted."""


@dataclass(frozen=True, slots=True)
class TokenClaims:
    user_id: UUID
    issued_at: datetime
    expires_at: datetime


def create_access_token(
    user_id: UUID,
    secret: str,
    issuer: str,
    lifetime_minutes: int,
    now: datetime | None = None,
) -> str:
    issued_at = now or datetime.now(UTC)
    expires_at = issued_at + timedelta(minutes=lifetime_minutes)
    return jwt.encode(
        {
            "sub": str(user_id),
            "iss": issuer,
            "iat": issued_at,
            "exp": expires_at,
            "type": "access",
        },
        secret,
        algorithm="HS256",
    )


def decode_access_token(token: str, secret: str, issuer: str) -> TokenClaims:
    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            issuer=issuer,
            options={"require": ["sub", "iss", "iat", "exp", "type"]},
        )
        if payload["type"] != "access":
            raise TokenError("Token type is not accepted.")
        return TokenClaims(
            user_id=UUID(payload["sub"]),
            issued_at=datetime.fromtimestamp(payload["iat"], UTC),
            expires_at=datetime.fromtimestamp(payload["exp"], UTC),
        )
    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError) as exc:
        raise TokenError("Access token is invalid or expired.") from exc
