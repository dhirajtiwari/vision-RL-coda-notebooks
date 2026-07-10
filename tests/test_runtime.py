"""Unit tests for reusable runtime primitives (cache, concurrency, partitioning)."""

from __future__ import annotations

import time

from runtime.cache import TtlCache, get_named_cache, invalidate_all_named_caches
from runtime.concurrency import parallel_map
from runtime.partitioning import (
    PartitionKey,
    batch_items,
    partition_for_etl,
    partition_for_rate_limit,
    partition_for_request,
)


def test_ttl_cache_hit_and_miss():
    cache: TtlCache[str, int] = TtlCache(ttl_seconds=60, maxsize=8, name="t")
    assert cache.get("a") is None
    cache.set("a", 1)
    assert cache.get("a") == 1
    assert cache.stats.hits == 1
    assert cache.stats.misses == 1


def test_ttl_cache_expiry():
    cache: TtlCache[str, str] = TtlCache(ttl_seconds=0.05, maxsize=4, name="exp")
    cache.set("k", "v")
    assert cache.get("k") == "v"
    time.sleep(0.07)
    assert cache.get("k") is None


def test_ttl_cache_maxsize_eviction():
    cache: TtlCache[str, int] = TtlCache(ttl_seconds=60, maxsize=2, name="cap")
    cache.set("a", 1)
    cache.set("b", 2)
    cache.set("c", 3)
    assert len(cache) == 2
    assert cache.stats.evictions >= 1


def test_get_or_set_factory_runs_once():
    cache: TtlCache[str, int] = TtlCache(ttl_seconds=60, maxsize=4, name="gos")
    calls = {"n": 0}

    def factory() -> int:
        calls["n"] += 1
        return 42

    assert cache.get_or_set("x", factory) == 42
    assert cache.get_or_set("x", factory) == 42
    assert calls["n"] == 1


def test_named_cache_invalidation():
    c = get_named_cache("unit_test_named", ttl_seconds=60, maxsize=4)
    c.set("k", "v")
    invalidate_all_named_caches()
    assert c.get("k") is None


def test_parallel_map_preserve_order():
    out = parallel_map([3, 1, 2], lambda x: x * 10, max_workers=3)
    assert out == [30, 10, 20]


def test_parallel_map_single_worker_fallback():
    out = parallel_map([1, 2], lambda x: x + 1, max_workers=1)
    assert out == [2, 3]


def test_partition_keys():
    pk = PartitionKey(tenant_id="acme", product_id="wm-001", region="us-east")
    assert "tenant=acme" in pk.as_string()
    assert "product=wm-001" in pk.as_string()
    assert "tenant=acme" in partition_for_request(tenant_id="acme", product_id="wm-001")
    assert "route=/diagnose" in partition_for_rate_limit(client_key="ip", route="/diagnose")
    assert "batch=b1" in partition_for_etl(batch_id="b1", source_system="PIM")


def test_batch_items():
    assert batch_items([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]
    assert batch_items([1, 2, 3], 0) == [[1, 2, 3]]
    assert batch_items([], 2) == []
