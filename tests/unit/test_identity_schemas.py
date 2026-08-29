import pytest
from pydantic import ValidationError

from audittrail_api.identity.schemas import UserCreate


def test_user_email_is_normalized() -> None:
    payload = UserCreate(
        email="Auditor@Example.COM",
        display_name="Example Auditor",
        password="correct horse battery staple",  # noqa: S106
    )

    assert str(payload.email) == "auditor@example.com"


def test_short_password_is_rejected() -> None:
    with pytest.raises(ValidationError):
        UserCreate(
            email="user@example.com",
            display_name="User",
            password="too-short",  # noqa: S106
        )
