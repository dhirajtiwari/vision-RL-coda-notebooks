# 03 — Platform runtime

**Load when:** P5 caches, parallel extract, rate limit, admission, lineage.

## Must implement

| Capability | As-built default (this repo) | Notes |
|------------|------------------------------|--------|
| Parallel connector extract | 4 workers | Serial product transform |
| Ontology schema cache TTL | 300s | Named cache |
| Product subgraph cache TTL | 60s | Explorer |
| Diagnose result cache | ON, 90s, max 512 | Key = identity + catalog/version + message scope |
| Redis | Optional; memory if no URL | Multi-replica needs `REDIS_URL` |
| Rate limit | 60 / minute | API guardrails |
| Concurrent diagnose admission | 32 | Back-pressure |
| Neo4j pool | 50 | Driver settings |
| Cache invalidation | On successful load/promote | `invalidate_all_named_caches` pattern |
| Provenance stamps | ON | Configurable |
| OpenTelemetry | OFF by default | Optional |

## Prove it works

`GET /health` must expose a **`runtime`** object (cache modes, workers, redis backend, pool).

## Do not

- Parallelize a single diagnose ranking path “for performance” without evidence.
- Cache answers by raw message text alone.
- Leave stale diagnose cache after promote.

## As-built map

- `runtime/cache.py`, `runtime/diagnose_cache.py`, parallel_map / admission modules
- `guardrails/rate_limit.py`
- `services/diagnosis_service.py`
- Settings knobs in `config/settings.py`

## Exit (P5)

`/health.runtime` populated; invalidate-on-promote verified; rate/admission active.
