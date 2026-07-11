"""
Thread-safe TTL cache with hit/miss stats — in-process or Redis-backed.

Industry use (enterprise diagnosis APIs):
  - Cache *stable* reads: ontology schema, product subgraphs, catalog lookups.
  - Do NOT cache personalized diagnosis results without a strong key that includes
    message + product + asset + policy version (staleness + privacy risk).

Multi-replica: set ``REDIS_URL``; ``get_named_cache`` uses Redis when connected,
otherwise the same API falls back to in-process memory.
"""

from __future__ import annotations

import pickle
import threading
import time
from collections.abc import Callable, Hashable
from dataclasses import dataclass
from functools import wraps
from typing import Any, Protocol, TypeVar

from runtime.redis_client import get_redis_client, namespaced

V = TypeVar("V")


@dataclass
class CacheStats:
    hits: int = 0
    misses: int = 0
    sets: int = 0
    evictions: int = 0
    invalidations: int = 0

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return (self.hits / total) if total else 0.0

    def as_dict(self) -> dict[str, Any]:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "sets": self.sets,
            "evictions": self.evictions,
            "invalidations": self.invalidations,
            "hit_rate": round(self.hit_rate, 4),
        }


class CacheLike(Protocol[V]):
    name: str
    stats: CacheStats
    backend: str

    def get(self, key: Any, default: V | None = None) -> V | None: ...
    def set(self, key: Any, value: V, *, ttl_seconds: float | None = None) -> None: ...
    def get_or_set(self, key: Any, factory: Callable[[], V], *, ttl_seconds: float | None = None) -> V: ...
    def invalidate(self, key: Any | None = None) -> None: ...
    def __len__(self) -> int: ...


@dataclass
class _Entry[V]:
    value: V
    expires_at: float  # monotonic deadline; inf = no expiry


class TtlCache[K: Hashable, V]:
    """In-process TTL + LRU-ish capacity cache (thread-safe)."""

    backend = "memory"

    def __init__(
        self,
        *,
        ttl_seconds: float = 60.0,
        maxsize: int = 256,
        name: str = "cache",
    ) -> None:
        if ttl_seconds < 0:
            raise ValueError("ttl_seconds must be >= 0 (0 means no expiry)")
        if maxsize < 1:
            raise ValueError("maxsize must be >= 1")
        self.ttl_seconds = ttl_seconds
        self.maxsize = maxsize
        self.name = name
        self._store: dict[K, _Entry[V]] = {}
        self._lock = threading.RLock()
        self.stats = CacheStats()

    def _expired(self, entry: _Entry[V], now: float) -> bool:
        return now >= entry.expires_at

    def get(self, key: K, default: V | None = None) -> V | None:
        now = time.monotonic()
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                self.stats.misses += 1
                return default
            if self._expired(entry, now):
                del self._store[key]
                self.stats.evictions += 1
                self.stats.misses += 1
                return default
            self._store[key] = entry
            self.stats.hits += 1
            return entry.value

    def set(self, key: K, value: V, *, ttl_seconds: float | None = None) -> None:
        ttl = self.ttl_seconds if ttl_seconds is None else ttl_seconds
        expires = time.monotonic() + ttl if ttl > 0 else float("inf")
        with self._lock:
            if key not in self._store and len(self._store) >= self.maxsize:
                oldest = next(iter(self._store))
                del self._store[oldest]
                self.stats.evictions += 1
            self._store[key] = _Entry(value=value, expires_at=expires)
            self.stats.sets += 1

    def get_or_set(self, key: K, factory: Callable[[], V], *, ttl_seconds: float | None = None) -> V:
        hit = self.get(key)
        if hit is not None:
            return hit
        value = factory()
        self.set(key, value, ttl_seconds=ttl_seconds)
        return value

    def invalidate(self, key: K | None = None) -> None:
        with self._lock:
            if key is None:
                n = len(self._store)
                self._store.clear()
                self.stats.invalidations += n
            elif key in self._store:
                del self._store[key]
                self.stats.invalidations += 1

    def __len__(self) -> int:
        with self._lock:
            return len(self._store)


class RedisTtlCache[V]:
    """
    Redis-backed TTL cache with the same public surface as TtlCache.

    Values are pickle-serialized. On any Redis error, operations degrade to a
    local memory cache so the API never fails closed on cache backend issues.
    """

    backend = "redis"

    def __init__(
        self,
        *,
        ttl_seconds: float = 60.0,
        maxsize: int = 256,
        name: str = "cache",
        client: Any | None = None,
    ) -> None:
        self.ttl_seconds = ttl_seconds
        self.maxsize = maxsize
        self.name = name
        self._client = client
        self._fallback: TtlCache[str, V] = TtlCache(ttl_seconds=ttl_seconds, maxsize=maxsize, name=f"{name}:mem")
        self.stats = CacheStats()
        self._lock = threading.RLock()

    def _redis(self) -> Any | None:
        return self._client if self._client is not None else get_redis_client()

    def _rkey(self, key: Any) -> str:
        return namespaced("cache", self.name, str(key))

    def get(self, key: Any, default: V | None = None) -> V | None:
        client = self._redis()
        if client is None:
            val = self._fallback.get(str(key), default)
            self.stats.hits = self._fallback.stats.hits
            self.stats.misses = self._fallback.stats.misses
            return val
        try:
            raw = client.get(self._rkey(key))
            if raw is None:
                self.stats.misses += 1
                return default
            self.stats.hits += 1
            return pickle.loads(raw)  # noqa: S301 - internal cache only
        except Exception:
            self.stats.misses += 1
            return self._fallback.get(str(key), default)

    def set(self, key: Any, value: V, *, ttl_seconds: float | None = None) -> None:
        ttl = self.ttl_seconds if ttl_seconds is None else ttl_seconds
        client = self._redis()
        if client is None:
            self._fallback.set(str(key), value, ttl_seconds=ttl)
            self.stats.sets += 1
            return
        try:
            payload = pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)
            rkey = self._rkey(key)
            if ttl and ttl > 0:
                client.set(rkey, payload, ex=max(1, int(ttl)))
            else:
                client.set(rkey, payload)
            self.stats.sets += 1
        except Exception:
            self._fallback.set(str(key), value, ttl_seconds=ttl)
            self.stats.sets += 1

    def get_or_set(self, key: Any, factory: Callable[[], V], *, ttl_seconds: float | None = None) -> V:
        hit = self.get(key)
        if hit is not None:
            return hit
        value = factory()
        self.set(key, value, ttl_seconds=ttl_seconds)
        return value

    def invalidate(self, key: Any | None = None) -> None:
        client = self._redis()
        self._fallback.invalidate(None if key is None else str(key))
        if client is None:
            if key is None:
                self.stats.invalidations += 1
            return
        try:
            if key is not None:
                client.delete(self._rkey(key))
                self.stats.invalidations += 1
                return
            pattern = namespaced("cache", self.name, "*")
            deleted = 0
            for rkey in client.scan_iter(match=pattern, count=200):
                client.delete(rkey)
                deleted += 1
            self.stats.invalidations += deleted
        except Exception:
            self.stats.invalidations += 1

    def __len__(self) -> int:
        # Approximate: memory fallback size only (Redis cardinality is expensive).
        return len(self._fallback)


# Process-wide named caches for shared invalidation (e.g. after ETL load).
_REGISTRY: dict[str, CacheLike[Any]] = {}
_REGISTRY_LOCK = threading.Lock()


def create_cache(
    name: str,
    *,
    ttl_seconds: float = 60.0,
    maxsize: int = 256,
    prefer_redis: bool = True,
) -> CacheLike[Any]:
    """Factory: Redis when configured+connected, else in-process TtlCache."""
    if prefer_redis:
        client = get_redis_client()
        if client is not None:
            return RedisTtlCache(ttl_seconds=ttl_seconds, maxsize=maxsize, name=name, client=client)
    return TtlCache(ttl_seconds=ttl_seconds, maxsize=maxsize, name=name)


def get_named_cache(
    name: str,
    *,
    ttl_seconds: float = 60.0,
    maxsize: int = 256,
) -> CacheLike[Any]:
    with _REGISTRY_LOCK:
        cache = _REGISTRY.get(name)
        if cache is None:
            cache = create_cache(name, ttl_seconds=ttl_seconds, maxsize=maxsize)
            _REGISTRY[name] = cache
        return cache


def invalidate_all_named_caches() -> None:
    with _REGISTRY_LOCK:
        for cache in _REGISTRY.values():
            cache.invalidate()


def cache_stats_snapshot() -> dict[str, dict[str, Any]]:
    with _REGISTRY_LOCK:
        return {
            name: c.stats.as_dict()
            | {
                "size": len(c),
                "backend": getattr(c, "backend", "memory"),
            }
            for name, c in _REGISTRY.items()
        }


def reset_named_caches_for_tests() -> None:
    """Clear registry (unit tests only)."""
    with _REGISTRY_LOCK:
        for cache in _REGISTRY.values():
            cache.invalidate()
        _REGISTRY.clear()


def cached(
    cache: CacheLike[Any],
    key_fn: Callable[..., Hashable] | None = None,
) -> Callable[[Callable[..., V]], Callable[..., V]]:
    """Decorator: memoize function results in a cache."""

    def decorator(fn: Callable[..., V]) -> Callable[..., V]:
        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> V:
            key: Hashable
            if key_fn is not None:
                key = key_fn(*args, **kwargs)
            else:
                key = (args, tuple(sorted(kwargs.items())))
            return cache.get_or_set(key, lambda: fn(*args, **kwargs))

        return wrapper

    return decorator
