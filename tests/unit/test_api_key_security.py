from audittrail_api.auth.security import generate_api_key, verify_api_key


def test_generated_api_key_can_be_verified() -> None:
    generated = generate_api_key("a-test-pepper-with-enough-length")

    assert generated.raw.startswith("at_live_")
    assert generated.raw.startswith(generated.prefix)
    assert verify_api_key(generated.raw, generated.digest, "a-test-pepper-with-enough-length")


def test_wrong_api_key_is_rejected() -> None:
    generated = generate_api_key("a-test-pepper-with-enough-length")

    assert not verify_api_key(
        "at_live_wrong-credential",
        generated.digest,
        "a-test-pepper-with-enough-length",
    )
