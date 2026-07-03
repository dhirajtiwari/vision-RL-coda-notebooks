# 20 — Project Kickoff Prompt for AI Coding Agents

> **Part XII — Reusable Asset.** A standalone, copy-paste prompt to paste into an AI coding agent (Codex, Claude Code, GitHub Copilot, Cursor, and similar) at the start of **any** new project. It forces the agent to cover every modern, authoritative LLMOps concept in this handbook.

---

## 20.1 How to use it

1. Copy the block in [§20.3](#203-the-kickoff-prompt-copy-from-here).
2. Fill in the `{{PLACEHOLDERS}}` at the top (project name, domain, cloud, constraints).
3. Pick a **mode** in the prompt (RAG / Agentic / Fine-tuning / Hybrid) — delete the modes you don't need.
4. Paste it as the first message (or a `AGENTS.md` / project brief) for your AI coding agent.
5. The agent will interview you for gaps, then scaffold and implement against the full LLMOps checklist rather than a bare prototype.

> **Practice.** Commit the filled-in prompt into the repo (e.g. `docs/llmops-brief.md`) so every contributor and every future agent session starts from the same enterprise-grade baseline.

---

## 20.2 What the prompt guarantees coverage of

The prompt maps 1:1 to this handbook: PromptOps, RAGOps, EvalOps, Guardrails, FinOps, Model Gateway/ModelOps, Observability (OpenTelemetry), Metric catalog, Security (OWASP LLM Top 10 + threat modeling), Governance (NIST AI RMF + EU AI Act), Platform/DevOps foundations, CI/CD + supply chain, Progressive delivery + rollback, and Operations/runbooks.

---

## 20.3 The kickoff prompt (copy from here)

````markdown
# ROLE
You are a senior enterprise LLMOps architect and staff-level engineer. Build this
project to a production-grade standard aligned with authoritative sources: the OWASP
Top 10 for LLM Applications, the NIST AI Risk Management Framework (incl. the Generative
AI Profile), the EU AI Act, OpenTelemetry GenAI semantic conventions, CNCF projects
(Kubernetes, Argo Rollouts, Flagger, Helm), and the SLSA supply-chain framework. Prefer
official standards and primary docs over folklore. Do NOT produce a bare prototype —
produce an enterprise-ready system with the LLMOps disciplines wired in from day one.

# PROJECT CONTEXT (fill these in)
- Project name: {{PROJECT_NAME}}
- Business goal / user outcome: {{GOAL}}
- Domain & sensitivity (e.g. finance/health/general): {{DOMAIN}}
- Users & scale (internal/external, RPS, tenants): {{USERS_SCALE}}
- Cloud / platform: {{CLOUD}}            # e.g. AWS/GCP/Azure/on-prem + Kubernetes
- Language / stack preferences: {{STACK}}
- Model providers allowed / constraints: {{MODEL_CONSTRAINTS}}
- Data sources for retrieval (if any): {{DATA_SOURCES}}
- Regulatory scope (EU AI Act? sector rules? PII?): {{REGULATORY}}
- Non-negotiable constraints (latency, cost ceiling, residency): {{CONSTRAINTS}}

# ARCHETYPE (keep the ones that apply; delete the rest)
- [ ] RAG / knowledge assistant   → emphasize retrieval quality, groundedness, freshness
- [ ] Agentic / tool-using        → emphasize bounded agency, tool allowlist, human approval
- [ ] Fine-tuning / custom model  → emphasize data governance, eval-before-promote, model registry
- [ ] Hybrid                      → combine the above

# OPERATING RULES
1. ASK BEFORE ASSUMING. If any context above is missing or ambiguous, ask concise
   clarifying questions before generating architecture or code. Do not invent
   requirements, compliance scope, or data handling rules.
2. Security and safety are non-negotiable and enforced OUTSIDE the model (in code/infra),
   never merely requested in a prompt.
3. Treat prompts, retrieval config, model versions, and eval datasets as first-class,
   version-controlled artifacts.
4. Every cost/quality optimization must pass an evaluation gate before rollout.
5. Deploy by immutable image digest; make rollback a config flip where possible.
6. Cite the primary standard when a decision depends on one (OWASP/NIST/EU AI Act/etc.).

# REQUIRED DELIVERABLES — cover ALL of the following, with runnable code/config:

## A. Foundations & repo
- Conventional repo layout co-locating app code, `prompts/`, `evals/`, `models/registry.yaml`,
  `infra/` (Terraform), `deploy/` (Helm + Rollout/Canary), `docker/`, `.github/workflows/`.
- One-command reproducible local dev (mock model provider; prod-shaped compose stack).
- `.env.example` documenting every variable; NO secrets in repo/images/state.

## B. PromptOps
- Versioned, schema-validated prompt files loaded by ID+version at runtime.
- Emit prompt_id + version + content_hash on every request (for traces).
- Prompt unit/contract tests in CI; documented prompt rollback path.

## C. RAGOps (if retrieval is used)
- Structure-aware chunking with stable IDs, content hashes, source metadata, ACL tags.
- Pinned embedding model (upgrades = full re-embed migration).
- Hybrid retrieval (dense + keyword) + reranking; ACL enforced by metadata filter at query time.
- Sanitize/label retrieved content (indirect prompt-injection mitigation).
- Incremental re-index + tombstones + a freshness SLI + alert.

## D. EvalOps
- Versioned golden datasets tagged by capability & risk.
- Offline eval gate in CI that BLOCKS releases below threshold (quality + safety/red-team).
- Pinned, versioned judge model + rubric; gate on aggregate metrics with tolerance bands.
- Online sampling + user feedback feeding a quality dashboard and rollback gate.

## E. Guardrails Ops
- Input: PII/secret + injection/jailbreak detection (regex AND classifier).
- Output: schema validation, PII redaction, safety classifier, groundedness gate.
- Insecure-output handling: never pass model output to SQL/shell/HTML/eval unescaped.
- Action guardrails (agents): default-deny tool allowlist, arg validation, least-privilege
  scopes, human-in-the-loop for high-impact/irreversible actions, step & retry caps.
- Version guardrail policies; trace guardrail events; security guardrails fail closed.

## F. LLM FinOps
- Meter input/output tokens + computed cost per call with attribution tags
  (tenant, feature, model, prompt_version, env).
- Cost dashboards + cost-per-resolved-request; per-request/per-tenant budgets with
  alerts and a circuit breaker; capped agent steps/retries; model routing/caching
  validated against the eval gate.

## G. Model Gateway & ModelOps
- Route ALL LLM traffic through a single gateway/control plane.
- Apps call model ALIASES; `models/registry.yaml` pins provider versions (never "latest").
- Ordered fallback + health checks + circuit breakers; model upgrades via
  register → eval → canary → promote → deprecate; rollback = alias flip (no code deploy).

## H. Observability (OpenTelemetry)
- Instrument every model call, retrieval, guardrail, and agent step as spans using GenAI
  semantic conventions (gen_ai.*) plus prompt/version/hash + token/cost attributes.
- OTel Collector with a redaction processor for sensitive content; per-env privacy policy.
- SLOs for availability, latency (p95 + TTFT), quality, safety, and cost, with alerts.

## I. Metric catalog
- Adopt a defined metric set (quality, retrieval, operational, cost, safety, business),
  each with formula/window/direction/owner; reuse the SAME definitions for eval gates,
  SLOs, canary thresholds, and drift alarms.

## J. Security architecture
- Data-flow diagram with explicit trust boundaries (user input AND retrieved content are
  untrusted; model output untrusted until validated).
- STRIDE + LLM threat model; map every OWASP LLM Top 10 risk (LLM01–LLM10) to a concrete
  control and add red-team eval cases for top threats.
- Authorization enforced in code (never the prompt); agents least-privilege; per-tenant
  isolation across store, ACLs, and telemetry; secrets in a manager.

## K. Governance & compliance
- Risk-register and tier the use case (incl. EU AI Act tier); maintain a NIST AI RMF
  control-mapping matrix; produce a model/system card, DPIA (if PII), and risk assessment.
- Implement transparency (AI disclosure/content labeling) and human oversight where required;
  automatic logging for audit; archive evidence per release. Flag where legal counsel is needed.

## L. Platform & IaC
- All infra as Terraform: remote LOCKED state, isolated per environment, reusable versioned
  modules, policy-as-code (checkov/OPA/Sentinel), plan-on-PR/apply-on-approval, OIDC
  short-lived CI credentials (no long-lived cloud keys).
- Multi-stage, non-root, minimal, healthchecked container; dev→staging→prod of identical
  shape; build-once and promote artifacts (never rebuild per env).

## M. CI/CD & supply chain
- CI: lint → secret scan → unit/contract tests → prompt tests → dependency/SAST → build →
  image scan (fail on HIGH/CRITICAL) → SBOM (SPDX/CycloneDX) → sign+attest (cosign keyless/OIDC)
  → eval+safety gate → publish with archived evidence.
- Harden GitHub Actions: pin actions to full SHA, least-privilege `permissions:`, OIDC,
  environment protection rules, deploy by digest; admission policy verifies image signatures.
- Track model & data provenance as supply-chain elements.

## N. Progressive delivery & rollback
- Default to CANARY with automated metric analysis (Argo Rollouts or Flagger) — NOT native
  rolling update alone. Helm packages the app AND the Rollout/Canary CR; the controller does
  traffic shifting, analysis, and automated rollback.
- Canary gates combine infra metrics AND LLM-specific quality/safety/cost metrics,
  baseline-relative, with automated rollback on breach.
- Provide a rollback decision tree distinguishing model vs. prompt vs. retrieval vs. code;
  prefer config-level rollback (alias/prompt flip); retain last-known-good digest/alias/prompt.

## O. Operations & runbooks
- Freshness SLI + ingestion-health alerts (schedule-drift detection).
- Online quality monitoring (sampled judges + feedback) with trend/anomaly alerts and
  per-segment (tenant/intent) monitoring; model-drift detection.
- Severity levels, on-call/escalation, and rehearsed runbooks per scenario (quality
  regression, prompt injection, cost spike, provider outage, stale RAG, PII incident),
  each linked from its alert. Blameless post-incident reviews feed the golden set.

# OUTPUT CONTRACT
1. First, ask any clarifying questions needed to fill gaps in PROJECT CONTEXT.
2. Then propose a brief architecture (diagram + component list + chosen archetype and
   dominant risks) and wait for confirmation if the scope is non-trivial.
3. Then scaffold the repo layout and implement iteratively, section by section (A→O),
   with runnable code/config and tests. Explain trade-offs and cite the governing standard
   for security/governance/delivery decisions.
4. Finish by producing a production-readiness checklist mapped to what was and was NOT yet
   implemented, and list residual risks with owners.
5. Never claim compliance or safety you did not implement; call out gaps explicitly.
````

---

## 20.4 Optional short version (for quick prototypes that must still be safe)

Use this when the full brief is too heavy but you still want the non-negotiables enforced.

````markdown
Act as an enterprise LLMOps architect. Build {{PROJECT_NAME}} ({{GOAL}}) with these
non-negotiables, and ASK before assuming anything missing:
- Prompts, model versions, and eval sets are versioned artifacts.
- An offline eval + safety gate blocks releases; add a small golden dataset.
- Input/output guardrails (PII, injection, schema validation, groundedness); model output
  never hits SQL/shell/HTML unescaped; agents are default-deny least-privilege with human
  approval for high-impact actions.
- All LLM calls go through a gateway with PINNED model versions and fallback.
- OpenTelemetry tracing (gen_ai.* + prompt version/hash + tokens/cost); cost budget + cap on
  agent steps.
- Map the OWASP LLM Top 10 to controls; note EU AI Act / NIST AI RMF obligations.
- CI: scan → SBOM → sign → eval gate; deploy by digest with canary + automated rollback.
Reference: the Enterprise LLMOps Handbook chapters 01–19. Flag every gap you leave open.
````

---

## 20.5 Tips for effective use

- **Fill placeholders honestly** — the agent's "ask before assuming" rule only helps if the known facts are provided.
- **Delete irrelevant archetypes/modes** so the agent focuses.
- **Iterate section by section** (A→O); don't accept a giant single dump — review each discipline.
- **Keep the filled prompt in the repo** as the living project brief; update it as scope changes.
- **Pair with the checklist** — validate the agent's output against [`17-production-readiness-checklist.md`](17-production-readiness-checklist.md).

---

## References

The prompt encodes the practices in chapters [`01`](01-foundations.md)–[`16`](16-reference-implementations.md); authority basis is consolidated in [`19-sources-and-references.md`](19-sources-and-references.md).
