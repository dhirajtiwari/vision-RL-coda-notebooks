"""
Reusable enterprise runtime primitives: caching, bounded concurrency, partitioning.

In-process by default; set ``REDIS_URL`` for multi-replica shared cache, rate
limits, budgets, and concurrency admission. See ``docs/16-Enterprise-Runtime-Capabilities.md``.
"""

from runtime.cache import RedisTtlCache, TtlCache, cached, create_cache
from runtime.concurrency import parallel_map
from runtime.concurrency_limit import ConcurrencyLimiter, ConcurrencyLimitExceeded
from runtime.partitioning import (
    PartitionKey,
    batch_items,
    partition_for_etl,
    partition_for_rate_limit,
    partition_for_request,
)
from runtime.redis_client import get_redis_client, redis_health

__all__ = [
    "TtlCache",
    "RedisTtlCache",
    "create_cache",
    "cached",
    "parallel_map",
    "ConcurrencyLimiter",
    "ConcurrencyLimitExceeded",
    "PartitionKey",
    "batch_items",
    "partition_for_etl",
    "partition_for_rate_limit",
    "partition_for_request",
    "get_redis_client",
    "redis_health",
]
