"""Deterministic event hashing and chain verification."""

import hashlib
import json
from collections.abc import Iterable
from typing import Any

from audittrail_api.events.models import AuditEvent
from audittrail_api.events.schemas import EventCreate

GENESIS_HASH = "0" * 64


def canonical_payload(payload: EventCreate) -> bytes:
    """Serialize meaningful event content in a stable, platform-neutral form."""

    content: dict[str, Any] = payload.model_dump(mode="json")
    return json.dumps(
        content,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode()


def content_digest(payload: EventCreate) -> str:
    return hashlib.sha256(canonical_payload(payload)).hexdigest()


def chained_digest(payload_digest: str, previous_hash: str | None) -> str:
    chain_input = f"{previous_hash or GENESIS_HASH}:{payload_digest}".encode()
    return hashlib.sha256(chain_input).hexdigest()


def verify_chain(events: Iterable[AuditEvent], initial_hash: str | None = None) -> bool:
    """Verify an ordered sequence from genesis or a retention checkpoint."""

    previous_hash = initial_hash
    for event in events:
        if event.previous_hash != previous_hash:
            return False
        if event.event_hash != chained_digest(event.content_hash, previous_hash):
            return False
        previous_hash = event.event_hash
    return True
