"""
Rate limiter (kickoff prompt §E/§F).

Sliding-window limiter keyed by client identity (admin token, customer id, or
source IP). Uses Redis when ``REDIS_URL`` is configured and reachable so multiple
API replicas share one budget; otherwise falls back to in-process memory.
"""

from __future__ import annotations

import logging
import threading
import time
from collections import defaultdict, deque
from typing import Any

logger = logging.getLogger("diagnostics.rate_limit")

# Lua: atomic sliding-window check-and-record.
# KEYS[1]=zset key  ARGV[1]=now  ARGV[2]=window_start  ARGV[3]=max  ARGV[4]=member  ARGV[5]=ttl
_REDIS_ALLOW_SCRIPT = """
redis.call('ZREMRANGEBYSCORE', KEYS[1], '-inf', ARGV[2])
local n = redis.call('ZCARD', KEYS[1])
if n >= tonumber(ARGV[3]) then
  local oldest = redis.call('ZRANGE', KEYS[1], 0, 0, 'WITHSCORES')
  if oldest[2] then
    return {0, oldest[2]}
  end
  return {0, ARGV[1]}
end
redis.call('ZADD', KEYS[1], ARGV[1], ARGV[4])
redis.call('EXPIRE', KEYS[1], tonumber(ARGV[5]))
return {1, 0}
"""


class RateLimiter:
    """Fixed-capacity sliding window over ``window_seconds`` (memory or Redis)."""

    def __init__(
        self,
        *,
        max_per_window: int = 60,
        window_seconds: float = 60.0,
        redis_client: Any | None = None,
        key_prefix: str = "diagnostics:ratelimit:",
        prefer_redis: bool = True,
    ) -> None:
        self.max_per_window = max_per_window
        self.window_seconds = window_seconds
        self._redis = redis_client
        self._prefer_redis = prefer_redis
        self._key_prefix = key_prefix
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()
        self.backend = "memory"

    @classmethod
    def from_settings(cls, app_settings: Any | None = None) -> RateLimiter:
        if app_settings is None:
            from config.settings import settings as app_settings

        from runtime.redis_client import get_redis_client, key_prefix

        client = get_redis_client() if getattr(app_settings, "redis_url", None) else None
        limiter = cls(
            max_per_window=int(getattr(app_settings, "rate_limit_per_minute", 60)),
            window_seconds=60.0,
            redis_client=client,
            key_prefix=key_prefix() + "ratelimit:",
            prefer_redis=True,
        )
        limiter.backend = "redis" if client is not None else "memory"
        return limiter

    def _client(self) -> Any | None:
        if not self._prefer_redis:
            return None
        if self._redis is not None:
            return self._redis
        from runtime.redis_client import get_redis_client

        return get_redis_client()

    def allow(self, key: str) -> bool:
        """Return True if the request is within budget; records the hit."""
        if self.max_per_window <= 0:  # disabled
            return True
        client = self._client()
        if client is not None:
            try:
                return self._allow_redis(client, key)
            except Exception as exc:  # noqa: BLE001
                logger.warning("redis rate limit failed, using memory: %s", exc)
        return self._allow_memory(key)

    def _allow_memory(self, key: str) -> bool:
        self.backend = "memory"
        now = time.monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            bucket = self._hits[key]
            while bucket and bucket[0] < cutoff:
                bucket.popleft()
            if len(bucket) >= self.max_per_window:
                return False
            bucket.append(now)
            return True

    def _allow_redis(self, client: Any, key: str) -> bool:
        self.backend = "redis"
        now = time.time()
        window_start = now - self.window_seconds
        rkey = f"{self._key_prefix}{key}"
        member = f"{now}:{threading.get_ident()}:{id(self)}"
        ttl = max(1, int(self.window_seconds) + 1)
        result = client.eval(
            _REDIS_ALLOW_SCRIPT,
            1,
            rkey,
            str(now),
            str(window_start),
            str(self.max_per_window),
            member,
            str(ttl),
        )
        # redis-py may return [1, 0] as list of ints/bytes
        allowed = int(result[0]) == 1
        return allowed

    def retry_after(self, key: str) -> int:
        """Seconds until the oldest hit in the window expires."""
        client = self._client()
        if client is not None:
            try:
                return self._retry_after_redis(client, key)
            except Exception:
                pass
        with self._lock:
            bucket = self._hits.get(key)
            if not bucket:
                return 0
            return max(0, int(self.window_seconds - (time.monotonic() - bucket[0])))

    def _retry_after_redis(self, client: Any, key: str) -> int:
        rkey = f"{self._key_prefix}{key}"
        now = time.time()
        client.zremrangebyscore(rkey, "-inf", now - self.window_seconds)
        oldest = client.zrange(rkey, 0, 0, withscores=True)
        if not oldest:
            return 0
        oldest_score = float(oldest[0][1])
        return max(0, int(self.window_seconds - (now - oldest_score)))
