"""
Bounded concurrent request admission (protect Neo4j / diagnosis under load).

Industry practice: limit in-flight expensive requests per process (and optionally
globally via Redis) so a traffic spike cannot open unbounded Bolt sessions.

Uses Redis INCR/DECR when available so multi-replica fleets share one ceiling;
falls back to a process-local semaphore.
"""

from __future__ import annotations

import logging
import threading
import time
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

logger = logging.getLogger("diagnostics.concurrency_limit")


class ConcurrencyLimitExceeded(Exception):
    """Raised when too many expensive requests are already in flight."""


class ConcurrencyLimiter:
    def __init__(
        self,
        *,
        max_in_flight: int = 32,
        redis_client: Any | None = None,
        key: str = "diagnostics:inflight:diagnose",
        lease_seconds: int = 120,
        prefer_redis: bool = True,
    ) -> None:
        self.max_in_flight = max_in_flight
        self._redis = redis_client
        self._key = key
        self._lease_seconds = lease_seconds
        self._prefer_redis = prefer_redis
        self._local = 0
        self._lock = threading.Lock()
        self.backend = "memory"

    @classmethod
    def from_settings(cls, app_settings: Any | None = None) -> ConcurrencyLimiter:
        if app_settings is None:
            from config.settings import settings as app_settings

        from runtime.redis_client import get_redis_client, key_prefix

        client = get_redis_client() if getattr(app_settings, "redis_url", None) else None
        lim = cls(
            max_in_flight=int(getattr(app_settings, "max_concurrent_diagnoses", 32)),
            redis_client=client,
            key=key_prefix() + "inflight:diagnose",
            lease_seconds=int(getattr(app_settings, "diagnose_lease_seconds", 120)),
            prefer_redis=True,
        )
        lim.backend = "redis" if client is not None else "memory"
        return lim

    def _client(self) -> Any | None:
        if not self._prefer_redis:
            return None
        if self._redis is not None:
            return self._redis
        from runtime.redis_client import get_redis_client

        return get_redis_client()

    def try_acquire(self) -> str | None:
        """Acquire a slot; return lease token or None if rejected."""
        if self.max_in_flight <= 0:
            return "unlimited"
        client = self._client()
        if client is not None:
            try:
                return self._acquire_redis(client)
            except ConcurrencyLimitExceeded:
                return None
            except Exception as exc:  # noqa: BLE001
                logger.warning("redis concurrency acquire failed, using memory: %s", exc)
        return self._acquire_memory()

    def release(self, token: str | None) -> None:
        if not token or token == "unlimited":
            return
        client = self._client()
        if token.startswith("r:") and client is not None:
            try:
                client.decr(self._key)
                return
            except Exception as exc:  # noqa: BLE001
                logger.warning("redis concurrency release failed: %s", exc)
        with self._lock:
            self._local = max(0, self._local - 1)
            self.backend = "memory"

    def _acquire_memory(self) -> str | None:
        with self._lock:
            self.backend = "memory"
            if self._local >= self.max_in_flight:
                return None
            self._local += 1
            return f"m:{uuid.uuid4().hex}"

    def _acquire_redis(self, client: Any) -> str:
        self.backend = "redis"
        n = int(client.incr(self._key))
        client.expire(self._key, self._lease_seconds)
        if n > self.max_in_flight:
            client.decr(self._key)
            raise ConcurrencyLimitExceeded(f"max concurrent diagnoses {self.max_in_flight}")
        return f"r:{uuid.uuid4().hex}:{time.time()}"

    @contextmanager
    def slot(self) -> Iterator[None]:
        token = self.try_acquire()
        if token is None:
            raise ConcurrencyLimitExceeded(f"max concurrent diagnoses {self.max_in_flight}")
        try:
            yield
        finally:
            self.release(token)
