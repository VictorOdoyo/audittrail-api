from unittest.mock import AsyncMock

import pytest

from audittrail_api.auth.rate_limit import RATE_LIMIT_SCRIPT, consume_rate_limit


@pytest.mark.asyncio
async def test_rate_limit_reports_remaining_capacity() -> None:
    redis = AsyncMock()
    redis.eval.return_value = [3, 42]

    result = await consume_rate_limit(redis, "key-1", limit=5, window_seconds=60)

    assert result.allowed is True
    assert result.remaining == 2
    assert result.retry_after == 42
    redis.eval.assert_awaited_once_with(
        RATE_LIMIT_SCRIPT,
        1,
        "audittrail:rate-limit:key-1",
        60,
    )


@pytest.mark.asyncio
async def test_rate_limit_blocks_exhausted_window() -> None:
    redis = AsyncMock()
    redis.eval.return_value = [6, -1]

    result = await consume_rate_limit(redis, "key-1", limit=5, window_seconds=60)

    assert result.allowed is False
    assert result.remaining == 0
    assert result.retry_after == 1
