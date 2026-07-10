"""
Optional Redis client for multi-replica shared state.

When ``settings.redis_url`` is empty or Redis is unreachable, callers fall back
to in-process memory stores. The redis package is optional at import time so the
local demo still boots without it; install via ``requirements.txt`` for production.
"""

from __future__ import annotations

import logging
import threading
from typing import Any, Protocol

logger = logging.getLogger("diagnostics.redis")

_client: Any | None = None
_client_failed: bool = False
_lock = threading.Lock()


class RedisLike(Protocol):
    def ping(self) -> Any: ...
    def get(self, name: str) -> Any: ...
    def set(self, name: str, value: Any, ex: int | None = None, px: int | None = None) -> Any: ...
    def delete(self, *names: str) -> Any: ...
    def scan_iter(self, match: str | None = None, count: int | None = None) -> Any: ...
    def zadd(self, name: str, mapping: dict) -> Any: ...
    def zremrangebyscore(self, name: str, min: Any, max: Any) -> Any: ...
    def zcard(self, name: str) -> int: ...
    def zrange(self, name: str, start: int, end: int, withscores: bool = False) -> Any: ...
    def expire(self, name: str, time: int) -> Any: ...
    def incrbyfloat(self, name: str, amount: float = 1.0) -> float: ...
    def eval(self, script: str, numkeys: int, *keys_and_args: Any) -> Any: ...


def redis_configured() -> bool:
    try:
        from config.settings import settings

        return bool(getattr(settings, "redis_url", None))
    except Exception:
        return False


def get_redis_client(*, force_reconnect: bool = False) -> Any | None:
    """Return a live Redis client, or None if disabled / unavailable."""
    global _client, _client_failed

    if not redis_configured():
        return None

    with _lock:
        if force_reconnect:
            _client = None
            _client_failed = False
        if _client is not None:
            return _client
        if _client_failed and not force_reconnect:
            return None

        try:
            import redis  # type: ignore[import-untyped]
        except ImportError:
            logger.warning("redis package not installed; using in-process stores")
            _client_failed = True
            return None

        from config.settings import settings

        try:
            client = redis.Redis.from_url(
                settings.redis_url,
                decode_responses=False,
                socket_connect_timeout=float(settings.redis_connect_timeout_seconds),
                socket_timeout=float(settings.redis_socket_timeout_seconds),
                health_check_interval=30,
            )
            client.ping()
            _client = client
            _client_failed = False
            logger.info("redis connected url=%s", _redact_url(settings.redis_url))
            return _client
        except Exception as exc:  # noqa: BLE001
            logger.warning("redis unavailable (%s); falling back to in-process stores", exc)
            _client = None
            _client_failed = True
            return None


def close_redis_client() -> None:
    global _client, _client_failed
    with _lock:
        if _client is not None:
            import contextlib

            with contextlib.suppress(Exception):  # pragma: no cover
                _client.close()
        _client = None
        _client_failed = False


def redis_health() -> dict[str, Any]:
    """Status payload for /health."""
    from config.settings import settings

    configured = bool(getattr(settings, "redis_url", None))
    if not configured:
        return {
            "configured": False,
            "connected": False,
            "mode": "memory",
            "key_prefix": getattr(settings, "redis_key_prefix", "diagnostics:"),
        }
    client = get_redis_client()
    if client is None:
        return {
            "configured": True,
            "connected": False,
            "mode": "memory_fallback",
            "key_prefix": settings.redis_key_prefix,
        }
    try:
        client.ping()
        return {
            "configured": True,
            "connected": True,
            "mode": "redis",
            "key_prefix": settings.redis_key_prefix,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "configured": True,
            "connected": False,
            "mode": "memory_fallback",
            "error": str(exc),
            "key_prefix": settings.redis_key_prefix,
        }


def key_prefix() -> str:
    from config.settings import settings

    return getattr(settings, "redis_key_prefix", "diagnostics:") or "diagnostics:"


def namespaced(*parts: str) -> str:
    return key_prefix() + ":".join(parts)


def _redact_url(url: str) -> str:
    if "@" not in url:
        return url
    try:
        scheme, rest = url.split("://", 1)
        creds, host = rest.rsplit("@", 1)
        if ":" in creds:
            user = creds.split(":", 1)[0]
            return f"{scheme}://{user}:***@{host}"
        return f"{scheme}://***@{host}"
    except Exception:
        return "redis://***"
