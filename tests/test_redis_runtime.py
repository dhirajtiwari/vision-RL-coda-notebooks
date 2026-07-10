"""Tests for Redis-backed runtime stores (memory fallback + optional live Redis)."""

from __future__ import annotations

import time
from typing import Any
from unittest.mock import MagicMock

import pytest

from finops.budget import BudgetExceeded, DailyCostBudget
from guardrails.rate_limit import RateLimiter
from runtime.cache import RedisTtlCache, TtlCache, create_cache, reset_named_caches_for_tests
from runtime.concurrency_limit import ConcurrencyLimiter, ConcurrencyLimitExceeded
from runtime.redis_client import redis_health


@pytest.fixture(autouse=True)
def _clean_named_caches():
    reset_named_caches_for_tests()
    yield
    reset_named_caches_for_tests()


def test_create_cache_defaults_to_memory_without_redis(monkeypatch):
    monkeypatch.setattr("runtime.cache.get_redis_client", lambda: None)
    cache = create_cache("unit_mem", ttl_seconds=30, maxsize=8)
    assert isinstance(cache, TtlCache)
    assert cache.backend == "memory"
    cache.set("a", {"x": 1})
    assert cache.get("a") == {"x": 1}


def test_redis_ttl_cache_with_mock_client():
    store: dict[bytes, bytes] = {}

    client = MagicMock()

    def _get(k):
        return store.get(k if isinstance(k, bytes) else k.encode() if isinstance(k, str) else k)

    def _set(k, v, ex=None):
        key = k if isinstance(k, bytes) else k.encode() if isinstance(k, str) else k
        store[key] = v
        return True

    def _delete(*keys):
        for k in keys:
            key = k if isinstance(k, bytes) else k.encode() if isinstance(k, str) else k
            store.pop(key, None)
        return 1

    def _scan_iter(match=None, count=None):
        prefix = (match or "*").replace("*", "")
        for k in list(store):
            ks = k.decode() if isinstance(k, bytes) else k
            if ks.startswith(prefix.rstrip("*")) or match == "*":
                yield k

    client.get.side_effect = _get
    client.set.side_effect = _set
    client.delete.side_effect = _delete
    client.scan_iter.side_effect = _scan_iter

    cache: RedisTtlCache[Any] = RedisTtlCache(name="mock", ttl_seconds=60, client=client)
    cache.set("prod", {"nodes": [1]})
    assert cache.get("prod") == {"nodes": [1]}
    assert cache.stats.hits >= 1
    cache.invalidate("prod")
    assert cache.get("prod") is None


def test_rate_limiter_memory_path():
    lim = RateLimiter(max_per_window=2, window_seconds=60, prefer_redis=False)
    assert lim.allow("a")
    assert lim.allow("a")
    assert lim.allow("a") is False


def test_rate_limiter_redis_script_path():
    client = MagicMock()
    # First two allows, then block
    client.eval.side_effect = [[1, 0], [1, 0], [0, time.time()]]
    lim = RateLimiter(max_per_window=2, window_seconds=60, redis_client=client, prefer_redis=True)
    assert lim.allow("k") is True
    assert lim.allow("k") is True
    assert lim.allow("k") is False
    assert lim.backend == "redis"


def test_budget_memory_and_redis():
    b = DailyCostBudget(ceiling_usd=1.0, prefer_redis=False)
    b.check()
    b.record(1.0)
    with pytest.raises(BudgetExceeded):
        b.check()

    client = MagicMock()
    client.get.return_value = b"0.5"
    client.incrbyfloat.return_value = 1.5
    rb = DailyCostBudget(ceiling_usd=1.0, redis_client=client, prefer_redis=True)
    rb.check()  # 0.5 < 1.0
    rb.record(1.0)
    client.get.return_value = b"1.5"
    with pytest.raises(BudgetExceeded):
        rb.check()


def test_concurrency_limiter_memory():
    lim = ConcurrencyLimiter(max_in_flight=1, prefer_redis=False)
    t1 = lim.try_acquire()
    assert t1 is not None
    assert lim.try_acquire() is None
    lim.release(t1)
    assert lim.try_acquire() is not None


def test_concurrency_limiter_context():
    lim = ConcurrencyLimiter(max_in_flight=1, prefer_redis=False)
    with lim.slot(), pytest.raises(ConcurrencyLimitExceeded), lim.slot():
        pass


def test_redis_health_unconfigured():
    h = redis_health()
    assert "configured" in h
    assert "mode" in h
