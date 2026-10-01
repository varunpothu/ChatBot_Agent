import os

import pytest

from infra.redis_runtime import RedisSlidingWindowLimiter, RedisTTLCache

pytestmark = pytest.mark.integration


def test_redis_cache_and_shared_rate_limit():
    url = os.getenv("REDIS_URL")
    if not url:
        pytest.skip("REDIS_URL is not configured")

    cache = RedisTTLCache(url, ttl_seconds=30, namespace="coachai:test")
    key = cache.key("integration", "one")
    cache.set(key, {"ok": True})
    assert cache.get(key) == {"ok": True}

    limiter = RedisSlidingWindowLimiter(url, max_requests=2, window_seconds=30)
    assert limiter.allow("integration-test") is True
    assert limiter.allow("integration-test") is True
    assert limiter.allow("integration-test") is False
