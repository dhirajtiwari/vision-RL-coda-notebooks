# ADR 0001 — Adopt the Enterprise LLMOps disciplines on a deterministic core

- **Status:** Accepted
- **Date:** 2026-07-03
- **Deciders:** Platform, Diagnostics Product

## Context
The remote-diagnostics system is **graph-native and deterministic** (Neo4j +
FMEA/Bayesian inference), not a token-generating LLM app. We still want it to be
enterprise-grade per the Enterprise LLMOps Handbook (kickoff prompt §A–O), and we
plan to optionally add an LLM (OpenAI + Azure AI Foundry) later.

## Decision
Adopt the handbook disciplines, adapted to a deterministic core:
1. Keep the existing top-level package layout (do **not** reorg to `src/`).
2. Add discipline landing zones: `observability/`, `guardrails/`, `gateway/`,
   `finops/`, `promptops/`, `prompts/`, `evals/`, `models/`, `security/`,
   `monitoring/`, `infra/`, `deploy/`, `docs/{governance,runbooks,model-cards,adr}`.
3. Make LLM disciplines (PromptOps, Gateway, FinOps) **ready-but-inactive**
   (`LLM_ENABLED=false`) so activation is a config flip, not a re-architecture.
4. Enforce security/quality **outside the model**: input/output/action guardrails,
   a gated eval harness, OTel + Prometheus, PII redaction.
5. Infra as **multi-cloud Terraform placeholders**; real runtime stays local Docker.
6. Progressive delivery via **both** Argo Rollouts and Flagger, configurable.

## Consequences
- Enterprise operability (observability, guardrails, evals, runbooks) without paying
  LLM cost/complexity until needed.
- Some folders are intentionally scaffolds (infra placeholders, deploy CRs) pending
  a real cloud target.
- The eval gate + safety suite now block regressions in CI.

## Alternatives considered
- **Bare prototype:** rejected — not enterprise-grade.
- **Full `src/` reorg:** rejected — high churn/risk for no functional gain.
- **Activate LLM now:** deferred — core is deterministic; avoids premature cost/risk.
