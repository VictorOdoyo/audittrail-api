"""Argon2 password hashing with upgrade detection."""

from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()
DUMMY_HASH = password_hash.hash("audittrail-dummy-password")


def hash_password(password: str) -> str:
    """Hash a validated password using the current recommended algorithm."""

    return password_hash.hash(password)


def verify_password(password: str, stored_hash: str) -> tuple[bool, str | None]:
    """Verify a password and return an upgraded hash when parameters changed."""

    return password_hash.verify_and_update(password, stored_hash)


def consume_dummy_verification(password: str) -> None:
    """Reduce account-enumeration timing differences for unknown emails."""

    password_hash.verify(password, DUMMY_HASH)
