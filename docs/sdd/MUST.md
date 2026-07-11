# MUST (platform non-negotiables)

Unless `OVERRIDES.md` **explicitly** changes a line, agents implement these.

## Topology

- MUST run **dual graph**: production (chat/explore read) + staging (promote-first MERGE).
- MUST promote **staging then production** with explicit `target_env`.
- MUST keep diagnose / online read path on **production only**.

## Ontology

- MUST keep a **shared TBox** (classes + allowed relationships) defined once in code (exportable to Turtle/OWL).
- MUST build **ABox instances** only via pipeline from sources (structured / semi / unstructured).
- MUST shape-validate selection ABox against TBox before promote.
- MUST treat NEW product packs as ABox under existing classes — not a new schema.

## Ingest / control plane

- MUST support operator sequence: Sources → Fetch → Select → Validate → Materialize → Smoke → Approve → Promote → (optional) session reset.
- MUST implement selection-scoped materialize/promote (selected IDs only).
- MUST fail closed when selection is empty but actionable work exists.
- MUST run parallel connector extract, **serial** transform (default pattern).
- MUST retain durable lineage/audit of pipeline and admin actions.

## Runtime

- MUST expose `/health` with a **runtime** block (caches, workers, redis mode, pool).
- MUST use named caches with TTLs + invalidate after successful load/promote.
- MUST apply rate limit + concurrent diagnose admission (defaults may vary; knobs exist).
- MUST scope diagnose cache keys by identity + catalog/version, not message text alone.

## CI / honesty

- MUST have CI gates for pack-under-TBox discipline (no inventing unknown shapes silently).
- MUST label demo/fixture data vs live paths honestly.
- MUST keep `AS_BUILT.md` code-true after each completed phase.

## Carry-forward platform value (do not throw away)

1. Dual graph env
2. Selection-scoped promote + human smoke/approve
3. Parallel extract / serial transform
4. TTL caches + invalidate on publish
5. Rate limit + admission control
6. Lineage + admin audit
7. Shared TBox + ABox-from-pipeline
8. Asset/identity-first online path when CRM exists
9. Fail-closed empty selection
10. CI pack-under-TBox tests
