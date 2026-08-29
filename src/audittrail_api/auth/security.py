"""Generation and verification helpers for API keys."""

import hashlib
import hmac
import secrets
from dataclasses import dataclass
from uuid import UUID

KEY_MARKER = "at_live_"


@dataclass(frozen=True, slots=True)
class GeneratedAPIKey:
    raw: str
    prefix: str
    digest: str


@dataclass(frozen=True, slots=True)
class APIKeyPrincipal:
    key_id: UUID
    organization_id: UUID
    application_id: UUID
    scopes: frozenset[str]


def derive_digest(raw_key: str, pepper: str) -> str:
    """Derive a stable, non-reversible API-key digest."""

    return hmac.new(pepper.encode(), raw_key.encode(), hashlib.sha256).hexdigest()


def generate_api_key(pepper: str) -> GeneratedAPIKey:
    """Create a high-entropy credential and its safe storage representation."""

    secret = secrets.token_urlsafe(32)
    raw = f"{KEY_MARKER}{secret}"
    prefix = raw[:15]
    return GeneratedAPIKey(raw=raw, prefix=prefix, digest=derive_digest(raw, pepper))


def verify_api_key(raw_key: str, expected_digest: str, pepper: str) -> bool:
    """Compare a submitted key without leaking digest timing information."""

    return hmac.compare_digest(derive_digest(raw_key, pepper), expected_digest)
