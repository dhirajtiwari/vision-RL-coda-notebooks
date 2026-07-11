"""
Bounded concurrency for I/O-bound enterprise work.

Use cases that fit this product:
  - Parallel enterprise connector fetches (PIM/FSM/Claims/CRM).
  - Parallel product-subgraph warm-ups for dashboards.
  - Batch enrichment of many assets (CRM).

Do NOT use for:
  - Single-request diagnosis ranking (CPU work is light; correctness > parallelism).
  - Shared mutable Neo4j write sessions without isolation.
  - Unbounded fan-out that can overwhelm Neo4j or SaaS APIs.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed


def parallel_map[T, R](
    items: Sequence[T] | Iterable[T],
    fn: Callable[[T], R],
    *,
    max_workers: int = 4,
    preserve_order: bool = True,
) -> list[R]:
    """
    Run ``fn`` over items with a bounded thread pool.

    Exceptions from ``fn`` propagate after all submitted work finishes (or the
    first failure if ``preserve_order`` is False and a future raises early).
    """
    materialised = list(items)
    if not materialised:
        return []
    workers = max(1, min(max_workers, len(materialised)))
    if workers == 1 or len(materialised) == 1:
        return [fn(item) for item in materialised]

    with ThreadPoolExecutor(max_workers=workers) as pool:
        if preserve_order:
            futures = [pool.submit(fn, item) for item in materialised]
            return [f.result() for f in futures]

        futures = {pool.submit(fn, item): idx for idx, item in enumerate(materialised)}
        results: list[R | None] = [None] * len(materialised)
        for fut in as_completed(futures):
            idx = futures[fut]
            results[idx] = fut.result()
        return [r for r in results if r is not None]  # type: ignore[misc]
