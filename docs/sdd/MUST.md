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
- MUST harden the image supply chain before publish: **vulnerability scan** (fail HIGH/CRITICAL), **SBOM + provenance** attestation, and a keyless **signature** (cosign/OIDC); plus **SAST** (e.g. CodeQL) and managed dependency updates (e.g. Dependabot). See `04-PLATFORM-CI.md`.

## LLMOps (platform — ADR 0001)

- MUST keep the **deterministic core** as the default diagnose path unless OVERRIDES activates LLM-primary.
- MUST implement **Tier 1** before claiming enterprise readiness: observability, guardrails, eval gate, security artifacts, runbooks.
- MUST enforce input/output/action guardrails **outside** the model (code), fail-closed on injection/jailbreak.
- MUST rate-limit the public diagnose path; default memory backend, Redis for multi-replica.
- MUST redaction-enable PII for logs/telemetry/responses by default (`enable_pii_redaction`).
- MUST keep eval suites versioned (`evals/golden`, `evals/safety`) with floors in `thresholds.yaml`; **safety_pass = 1.0**.
- MUST **calibrate** eval floors against the real engine (measure, floor below measured) and **red-team the guardrails** (verify each attack blocks; verify benign inputs pass with zero false positives).
- MUST run eval smoke in CI; full suite when graph available (nightly or release).
- MUST **prove observability end-to-end** when claimed active: a scrape config collects `/metrics`, a dashboard renders it, and alert rules load — not just an exposed endpoint.
- MUST keep LLM gateway **ready-but-inactive** by default (`llm_enabled=false`) for deterministic-core archetypes — activation is a config flip.
- MUST pin model aliases in `models/registry.yaml` when LLM is used (no `latest`).
- MUST meter token/cost and enforce daily budget when LLM path is active.
- MUST maintain threat model + OWASP LLM mapping + system/model card + governance notes.
- MUST maintain one runbook per major alert class (cost, latency, PII, injection, provider outage, quality, rag-stale).
- MUST document residual risks honestly; never claim compliance not implemented.

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
11. Guardrails + rate limit + PII redaction
12. Eval + safety gate in CI
13. Observability (JSON logs, metrics; OTEL opt-in) — **proven** (scrape + dashboard + rules), not just a `/metrics` endpoint
14. Ready-but-inactive model gateway / PromptOps / FinOps
15. Security docs + system card + runbooks
16. Hardened CI supply chain (scan + SBOM + sign + SAST) and calibrated eval floors + red-teamed guardrails
