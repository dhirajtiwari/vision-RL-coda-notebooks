"""
Logical partitioning keys for multi-tenant / multi-product enterprise scale.

In industry practice, "partitioning" for warranty diagnosis means:

1. **Data partition** — isolate catalog/graph data by tenant, brand, region, or
   product line so ETL and queries stay bounded (ISO-style equipment scopes).
2. **Work partition** — batch ETL by product_id slices; shard rate-limit and
   cache keys by customer/tenant.
3. **Physical partition** (later) — Neo4j fabric / multi-database, Redis
   cluster slots, Kafka partitions — same *keys*, different substrate.

This module standardises key shapes so rate limits, caches, and future sharding
agree. It does not require multi-node infrastructure today.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PartitionKey:
    """Canonical multi-dimensional partition identifier."""

    tenant_id: str = "default"
    product_id: str | None = None
    region: str | None = None
    brand: str | None = None

    def as_string(self) -> str:
        parts = [f"tenant={self.tenant_id}"]
        if self.region:
            parts.append(f"region={self.region}")
        if self.brand:
            parts.append(f"brand={self.brand}")
        if self.product_id:
            parts.append(f"product={self.product_id}")
        return "|".join(parts)

    def cache_namespace(self, resource: str) -> str:
        return f"{self.as_string()}|res={resource}"


def partition_for_request(
    *,
    tenant_id: str = "default",
    product_id: str | None = None,
    customer_id: str | None = None,
    asset_id: str | None = None,
) -> str:
    """Key for per-request caching / tracing scopes (not for diagnosis memoization of free text)."""
    bits = [f"tenant={tenant_id or 'default'}"]
    if product_id:
        bits.append(f"product={product_id}")
    if customer_id:
        bits.append(f"customer={customer_id}")
    if asset_id:
        bits.append(f"asset={asset_id}")
    return "|".join(bits)


def partition_for_rate_limit(
    *,
    client_key: str,
    route: str = "/diagnose",
    tenant_id: str = "default",
) -> str:
    """Align rate-limit buckets with tenant-aware multi-tenant deployment."""
    return f"tenant={tenant_id}|route={route}|client={client_key}"


def partition_for_etl(
    *,
    batch_id: str,
    source_system: str,
    product_id: str | None = None,
) -> str:
    """Lineage / work-unit key for ETL slices."""
    base = f"batch={batch_id}|source={source_system}"
    if product_id:
        return f"{base}|product={product_id}"
    return base


def batch_items[T](items: Sequence[T] | Iterable[T], size: int) -> list[list[T]]:
    """
    Partition a work list into fixed-size batches (ETL product chunks, bulk claims).

    ``size <= 0`` returns a single batch containing all items.
    """
    materialised = list(items)
    if size <= 0 or size >= len(materialised):
        return [materialised] if materialised else []
    return [materialised[i : i + size] for i in range(0, len(materialised), size)]


def product_id_from_record(record: dict[str, Any]) -> str | None:
    """Best-effort product_id extraction from connector / catalog records."""
    if "product_id" in record:
        return str(record["product_id"])
    product = record.get("product")
    if isinstance(product, dict) and product.get("product_id"):
        return str(product["product_id"])
    return None
