from audittrail_api.identity.passwords import (
    consume_dummy_verification,
    hash_password,
    verify_password,
)


def test_password_hash_round_trip() -> None:
    stored = hash_password("correct horse battery staple")

    valid, replacement = verify_password("correct horse battery staple", stored)

    assert valid is True
    assert replacement is None
    assert "correct horse" not in stored


def test_wrong_password_and_dummy_verification_are_safe() -> None:
    stored = hash_password("correct horse battery staple")

    valid, _ = verify_password("wrong password", stored)
    consume_dummy_verification("unknown account password")

    assert valid is False
