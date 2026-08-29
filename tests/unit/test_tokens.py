from datetime import UTC, datetime
from uuid import uuid4

import pytest

from audittrail_api.identity.tokens import TokenError, create_access_token, decode_access_token

SECRET = "a-test-jwt-secret-with-at-least-32-bytes"  # noqa: S105


def test_access_token_round_trip() -> None:
    user_id = uuid4()
    now = datetime.now(UTC).replace(microsecond=0)
    token = create_access_token(user_id, SECRET, "test-issuer", 15, now)

    claims = decode_access_token(token, SECRET, "test-issuer")

    assert claims.user_id == user_id
    assert claims.issued_at == now
    assert claims.expires_at > claims.issued_at


def test_token_with_wrong_signature_is_rejected() -> None:
    token = create_access_token(uuid4(), SECRET, "test-issuer", 15)

    with pytest.raises(TokenError):
        decode_access_token(token, "another-secret-with-at-least-32-bytes", "test-issuer")
