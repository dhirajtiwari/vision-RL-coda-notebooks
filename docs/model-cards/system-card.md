# System Card — Remote Diagnostics

> Kickoff prompt §K, handbook ch11. Describes capabilities, limits, and intended
> use of the diagnosis system (a "system card" since the core is deterministic,
> not a single ML model).

## Intended use
- **In scope:** diagnosing faults for supported home appliances and determining
  warranty eligibility, as an **assistive** tool for customers and support agents.
- **Out of scope:** safety-critical decisions, medical/legal advice, unsupported
  product categories, autonomous financial actions without human approval.

## How it works
- Deterministic GraphRAG over Neo4j: product detection → symptom retrieval
  (TF-IDF + lexical) → FMEA + naive-Bayes failure-mode ranking → parts prediction.
- Every output carries a **provenance trail** to source systems (PIM/FSM/Claims/CRM).
- Optional LLM rewriter (inactive) only rephrases the grounded result.

## Performance & evaluation
- Gated by `evals/` golden + safety suites (`evals/thresholds.yaml`).
- Confidence below the escalation threshold routes to a human specialist.

## Limitations
- Quality depends on graph freshness (see `docs/runbooks/rag-stale.md`).
- Coverage limited to onboarded products; novel failure modes may under-diagnose.
- Not a substitute for a qualified technician.

## Risk tier
- **EU AI Act:** provisionally **limited/minimal risk** (assistive, human oversight,
  no biometric/critical-infrastructure use). Confirm with legal; transparency:
  users are informed they are interacting with an automated diagnostic assistant.

## Governance
- Threat model: `security/threat-model.md`; OWASP mapping: `security/owasp-llm-mapping.md`.
- DPIA: `docs/governance/dpia.md`; data classification/retention alongside.
- Owner: Diagnostics Product + Platform. Review cadence: each release.
