# 09 — Platform LLMOps (disciplines)

**Load when:** guardrails, evals, observability, gateway/prompts, FinOps, security/governance, progressive delivery, or anything in the LLMOps handbook/playbook.
**Do not load the entire handbook into context** — use this module + code paths; open one handbook chapter only if you need recipe detail.

## Mental model (ADR 0001 — accepted)

| Principle | Meaning |
|-----------|---------|
| **Deterministic core** | Primary diagnose path = Neo4j GraphRAG + FMEA/Bayes — **not** token generation |
| **Optional LLM** | Gateway / PromptOps / FinOps **ready-but-inactive** (`LLM_ENABLED=false` by default) |
| **Enforce outside the model** | Security/quality in code & infra, never “please don’t leak PII” in a prompt alone |
| **Versioned artifacts** | Prompts, model aliases, eval sets, thresholds are git artifacts |
| **Gate non-determinism** | Eval + safety floors before release; rollback via flag/alias, not only redeploy |

Handbook is **project-agnostic**. Playbook is the **sequence**. **This SDD module + AS_BUILT** are code-true for *this* entity.

## Discipline map (as-built)

| Discipline | Handbook | Status | Package / artifacts |
|------------|----------|--------|---------------------|
| Observability | ch08–09 | **ACTIVE** | `observability/` — JSON logs, request_id, Prometheus, OTEL opt-in, PII redaction |
| Guardrails | ch05 | **ACTIVE** | `guardrails/` — input, output, action, rate limit, pipeline |
| EvalOps | ch04 | **ACTIVE** | `evals/` — `run_eval.py`, `thresholds.yaml`, `golden/`, `safety/` |
| Security | ch10 | **ACTIVE** (docs + code) | `security/threat-model.md`, `owasp-llm-mapping.md` + guardrails |
| Governance | ch11 | **ACTIVE** (docs) | `docs/governance/*`, `docs/model-cards/system-card.md`, `docs/adr/` |
| Monitoring / ops | ch09, ch15 | **ACTIVE** (configs) | `monitoring/*`, `docs/runbooks/*` |
| Model gateway / ModelOps | ch07 | **READY** (inactive) | `gateway/`, `models/registry.yaml` |
| PromptOps | ch02 | **READY** (inactive) | `promptops/`, `prompts/` (+ `_schema.json`) |
| FinOps | ch06 | **READY** (inactive path) | `finops/budget.py` — wired when LLM calls happen |
| RAGOps (graph) | ch03 adapted | **ACTIVE** as GraphRAG | `graph/`, dual Neo4j, provenance — not classic vector-only RAG |
| CI/CD supply chain | ch13 | **ACTIVE** | `ci.yml` (secret scan, CodeQL, Trivy fs+image, SBOM+provenance, cosign sign), `cd.yml` (eval-gate → deploy), `.github/dependabot.yml` |
| Progressive delivery | ch14 | **WIRED (needs cluster)** | `cd.yml` eval-gate + opt-in `deploy_strategy: canary` → `deploy/rollouts/` Argo analysis on quality metric + `deploy/policy/verify-images.yaml` |
| Platform / IaC | ch12 | **SCAFFOLD** | `infra/terraform/` placeholders; runtime = Docker |

## Settings knobs (as-built defaults)

| Setting | Default | Notes |
|---------|---------|-------|
| `llm_enabled` | **false** | Config flip to activate gateway path |
| `llm_provider` / `llm_model_alias` | openai / diagnosis-rewriter | Pinned via `models/registry.yaml` |
| `llm_cost_budget_usd_per_day` | 5.00 | FinOps circuit breaker |
| `rate_limit_per_minute` | 60 | Guardrails |
| `enable_pii_redaction` | true | Logs/telemetry/output |
| `max_response_chars` / `max_input_length` | 8000 / 2000 | Caps |
| `log_json` | true | Structured logs |
| `otel_enabled` | **false** | Opt-in OTEL |
| `enable_prometheus_metrics` | true | `/metrics` |

## Eval gate (non-negotiable)

```bash
python evals/run_eval.py --suite smoke    # PR / CI
python evals/run_eval.py --suite full --report eval-report.json  # nightly / release
```

| Suite | Role |
|-------|------|
| smoke | Safety always; golden if graph up — CI |
| full | Higher floors + escalation_correct — nightly with graph |

**Floors (as-built `thresholds.yaml`):** smoke `product_accuracy`/`confidence_pass` ≥ 0.66, `safety_pass` = **1.0**; full higher.
**NEVER** lower thresholds to go green — fix the regression.

CI: `.github/workflows/ci.yml` runs eval smoke; `eval-nightly.yml` full gate.

## Prove it, don't assume it (paid lessons)

| Claim | Not done until… |
|-------|----------------|
| “Observability is active” | a **scrape config** collects `/metrics`, a **dashboard** renders it, and alert **rules load** — verify targets `up`. A `/metrics` endpoint alone is a stub. As-built: `monitoring/prometheus/prometheus.yml`, `monitoring/grafana/provisioning/`, `docker/docker-compose.observability.yaml`; prod: `k8s/monitoring/` (ServiceMonitor + PrometheusRule). |
| “Eval floors are set” | floors are **calibrated** against the real engine (measure per-case confidence, floor **below** measured). Guessed floors are flaky or meaningless. |
| “Guardrails block attacks” | you **red-teamed** them: probe with candidate attacks, close the gaps found, and confirm benign inputs still pass (**zero false positives**). Add each verified attack to `evals/safety/` by class. |
| “Images are shippable” | scanned (fail HIGH/CRITICAL) + SBOM + signed (see `04-PLATFORM-CI.md`). |

## 2025 authoritative deltas (greenfield must-consider)

The kickoff contract (`docs/llmops-handbook/20-project-kickoff-prompt.md`) and `todo.md` §1.7 carry the current-standard items. When the LLM path or an agent is in scope, do **not** ship without deciding on each:

- **Security:** map **OWASP LLM Top 10 (2025)** explicitly; for tool-using agents add **OWASP Agentic AI Threats** + **MITRE ATLAS**; document provider **zero-retention / no-train** + residency.
- **EvalOps:** **groundedness/faithfulness** gate on any LLM output; **LLM-as-judge calibration** (agreement/bias/variance) before trusting a judge; **agent-trajectory** evals (tool choice/args/steps); contamination + determinism controls; per-segment fairness.
- **Guardrails:** injection **defense-in-depth** (delimit/spotlight untrusted content, planner/data privilege separation, treat tool + retrieval output as untrusted); **structured/constrained output**.
- **Governance:** maintain an **AI-BOM** (models, embeddings, prompts, datasets, judges); **EU AI Act Art. 14** human-oversight design + **Art. 73** serious-incident reporting procedure; content-provenance labeling (C2PA) where applicable.
- **Runtime:** cache keys include **tenant + ACL scope** (no cross-tenant completion leakage).

These are tracked as honest `[ ]` gaps in `todo.md` §1.7 — a greenfield fork inherits the checklist, not a false “done”.

## Tests that lock LLMOps

- `tests/test_guardrails.py` — injection/jailbreak/cypher, rate limit, action allowlist
- `tests/test_observability.py` — redaction, metrics, gateway inactive, budget
- Eval harness itself as gate

## API wiring (as-built)

`api/main.py`: request middleware for observability + rate limit; diagnose path runs input guardrails + output validation; OTEL instrument when enabled; Prometheus series for requests/LLM usage when called.

## Security & governance artifacts

| Artifact | Path |
|----------|------|
| Threat model (STRIDE) | `security/threat-model.md` |
| OWASP LLM Top 10 map | `security/owasp-llm-mapping.md` |
| DPIA / classification / retention | `docs/governance/` |
| System card | `docs/model-cards/system-card.md` |
| ADR adopt disciplines | `docs/adr/0001-adopt-llmops-disciplines.md` |
| Runbooks | `docs/runbooks/` — cost, latency, PII, injection, provider outage, quality, rag-stale |

## Progressive delivery / deploy (scaffold honesty)

- K8s base + staging/prod overlays under `deploy/`
- Argo Rollouts + Flagger canary manifests present
- Image verify / policy samples
- Terraform placeholders — **not** a full cloud landing zone

Do **not** claim live multi-cluster progressive delivery unless a real cluster is wired.

## Handbook / playbook usage (agents)

| Need | Open |
|------|------|
| Code-true status for this product | This file + `AS_BUILT.md` |
| Recipe / copy-paste pattern | One chapter under `docs/llmops-handbook/` |
| 9-step field sequence | `docs/llmops-handbook/LLMOPS-IMPLEMENTATION-PLAYBOOK.md` (human/planning; skim sections, don’t dump all) |
| Kickoff contract A–O | `docs/llmops-handbook/20-project-kickoff-prompt.md` |
| Repo tree blueprint | `docs/llmops-handbook/21-reference-repository-blueprint.md` |

## Tiering for greenfield (from playbook)

1. **Tier 1 (must):** observability, guardrails, evals, security, runbooks
2. **Tier 2:** progressive delivery, governance enforcement, hardened CI supply chain
3. **Tier 3:** PromptOps + Gateway + FinOps — **active** if LLM primary; else ready-but-inactive

## Exit gates

- [ ] Guardrails block injection/jailbreak in tests **and** were red-teamed (attacks blocked, benign pass, zero false positives)
- [ ] Eval smoke in CI; safety floor 1.0; floors **calibrated** against the real engine
- [ ] PII redaction on by default
- [ ] Rate limit + metrics path live **and observability proven** (scrape + dashboard + rules load, targets up)
- [ ] CI hardened: SAST + dep/IaC scan + image scan (fail HIGH/CRITICAL) + SBOM/provenance + cosign sign
- [ ] CD gated by the eval gate; progressive-delivery path present (canary on a quality metric) — not claimed “live” without a cluster
- [ ] LLM path off by default unless OVERRIDES says otherwise
- [ ] Model registry rejects `latest` if gateway used
- [ ] Threat model + OWASP map + system card present; 2025 deltas (agentic/AI-BOM/EU AI Act/groundedness) triaged in `todo.md` §1.7
- [ ] One runbook per alert class
- [ ] Residual risks listed honestly (no fake compliance)
