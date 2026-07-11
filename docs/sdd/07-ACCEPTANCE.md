# 07 — Acceptance gates

**Load when:** declaring parity, release readiness, or phase completion.
**Code truth:** if code fails a box, box stays unchecked — do not “pass” in prose.

## Platform (must for parity with as-built maturity)

- [ ] `docker compose` starts **prod graph + staging graph** (Redis optional)
- [ ] API `/health` reports both graphs + **runtime** block
- [ ] Pipeline registry: extract → materialize → smoke → promote
- [ ] Parallel extract, serial transform
- [ ] Selection-scoped materialize/promote; empty selection fail-closed when work exists
- [ ] Promote staging then production; diagnose reads **production only**
- [ ] Named caches + invalidate after promote/load
- [ ] Rate limit + concurrent admission
- [ ] Durable lineage/audit of pipeline/admin actions
- [ ] CI: lint + tests + pack-under-TBox + UI build + **eval smoke**
- [ ] Demo/live labeling for fixture data
- [ ] Anti-patterns in `NEVER.md` / `08-GAPS.md` team-reviewed
- [ ] **LLMOps Tier 1:** guardrails (input/output/action) + rate limit + PII redaction
- [ ] **LLMOps Tier 1:** structured logs + Prometheus metrics (+ OTEL opt-in)
- [ ] **LLMOps Tier 1:** eval golden + safety suites with floors; safety_pass = 1.0
- [ ] **LLMOps Tier 1:** threat model + OWASP map + system card + runbooks
- [ ] **LLMOps Tier 3:** gateway/PromptOps/FinOps present; default **LLM_ENABLED=false** unless OVERRIDES
- [ ] Residual risks listed honestly (no fake compliance claims)

## Domain (must for vertical demo)

- [ ] Shared TBox module (exportable)
- [ ] ≥1 multi-source ABox pack validated **without** a per-entity OWL file
- [ ] E2E promote + identity-bound query returns ranked result + steps + provenance
- [ ] Admin path: fetch → select → validate → materialize → smoke → approve → promote
- [ ] Idle/reset path after fleet in-sync

## Beyond parity

Use `08-GAPS.md`. Do **not** claim production multi-tenant SaaS until scoped **P0** gaps are closed.

## Sign-off

| Role | Date | Notes |
|------|------|-------|
| | | |
