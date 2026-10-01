from __future__ import annotations

import hashlib
import json
import os
import time
from typing import Any
from uuid import uuid4


class RedisTTLCache:
    """Shared JSON cache for multi-instance deployments.

    Values are intentionally JSON-only so cache contents stay inspectable and
    portable across application versions.
    """

    def __init__(self, url: str, ttl_seconds: int = 300, max_items: int = 512, namespace: str = "coachai"):
        import redis

        self.ttl_seconds = ttl_seconds
        self.max_items = max_items
        self.namespace = namespace
        self.client = redis.Redis.from_url(
            url,
            socket_connect_timeout=0.2,
            socket_timeout=0.2,
            retry_on_timeout=False,
        )

    @staticmethod
    def key(*parts: str) -> str:
        return hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()

    def _redis_key(self, key: str) -> str:
        return f"{self.namespace}:cache:{key}"

    def get(self, key: str) -> Any | None:
        raw = self.client.get(self._redis_key(key))
        if raw is None:
            return None
        return json.loads(raw)

    def set(self, key: str, value: Any) -> None:
        payload = json.dumps(value, separators=(",", ":"), ensure_ascii=False)
        self.client.setex(self._redis_key(key), self.ttl_seconds, payload)


class RedisSlidingWindowLimiter:
    """Atomic distributed sliding-window limiter using a Redis Lua script."""

    _SCRIPT = """
    local key=KEYS[1]
    local now=tonumber(ARGV[1])
    local window=tonumber(ARGV[2])
    local limit=tonumber(ARGV[3])
    local member=ARGV[4]
    redis.call('ZREMRANGEBYSCORE',key,0,now-window)
    local count=redis.call('ZCARD',key)
    if count >= limit then
        redis.call('EXPIRE',key,window)
        return 0
    end
    redis.call('ZADD',key,now,member)
    redis.call('EXPIRE',key,window)
    return 1
    """

    def __init__(self, url: str, max_requests: int = 30, window_seconds: int = 60):
        import redis

        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.fail_open = os.getenv("REDIS_RATE_LIMIT_FAIL_OPEN", "false").lower() == "true"
        self.client = redis.Redis.from_url(
            url,
            socket_connect_timeout=0.2,
            socket_timeout=0.2,
            retry_on_timeout=False,
        )
        self._script = self.client.register_script(self._SCRIPT)

    def allow(self, key: str) -> bool:
        now = time.time()
        redis_key = f"coachai:ratelimit:{key}"
        try:
            allowed = self._script(
                keys=[redis_key],
                args=[now, self.window_seconds, self.max_requests, uuid4().hex],
            )
            return bool(int(allowed))
        except Exception:
            return self.fail_open
