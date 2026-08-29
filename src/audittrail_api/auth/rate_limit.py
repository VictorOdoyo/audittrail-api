"""Atomic Redis-backed fixed-window rate limiting."""

from dataclasses import dataclass
from typing import Protocol, cast

RATE_LIMIT_SCRIPT = """
local current = redis.call('INCR', KEYS[1])
if current == 1 then
  redis.call('EXPIRE', KEYS[1], ARGV[1])
end
local ttl = redis.call('TTL', KEYS[1])
return {current, ttl}
"""


class ScriptRedis(Protocol):
    async def eval(self, script: str, numkeys: int, *keys_and_args: object) -> object: ...


@dataclass(frozen=True, slots=True)
class RateLimitResult:
    allowed: bool
    remaining: int
    retry_after: int


async def consume_rate_limit(
    redis: ScriptRedis,
    identifier: str,
    limit: int,
    window_seconds: int,
) -> RateLimitResult:
    """Increment one window atomically and report the caller's allowance."""

    raw_result = await redis.eval(
        RATE_LIMIT_SCRIPT,
        1,
        f"audittrail:rate-limit:{identifier}",
        window_seconds,
    )
    count, ttl = cast(list[int], raw_result)
    return RateLimitResult(
        allowed=count <= limit,
        remaining=max(0, limit - count),
        retry_after=max(1, ttl),
    )
