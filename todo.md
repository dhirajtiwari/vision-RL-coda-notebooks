# Remote Diagnostics Graph — Hardening & Grounding Plan

Goal: keep this a **demo that behaves like a production application**, with
**deterministic** product / problem / diagnostics / resolution / part prediction,
re-grounded in established reliability-engineering and diagnostic research so the
numbers are defensible instead of arbitrary magic constants.

## Research foundation (industry standards applied)
- **FMEA / FMECA** — MIL-STD-1629A; SAE J1739; **AIAG-VDA FMEA Handbook 2019**.
  Failure modes rated by **Severity (S) × Occurrence (O) × Detection (D)**; RPN = S·O·D.
  Ordinal-multiplication rank-reversal caveat (Kmenta & Ishii 2004) → also expose
  **Action Priority (High/Medium/Low)** as primary triage (AIAG-VDA replacement for RPN).
- **Bayesian diagnosis** — Pearl (1988); Russell & Norvig, *AIMA*. Given observed
  symptoms, compute posterior `P(fm|S) ∝ P(fm)·∏ᵢ P(sᵢ|fm)`, normalized across
  candidates → deterministic, reproducible ranking.
- **Empirical grounding** — occurrence prior derived from *observed* claim/resolution
  frequency (empirical Bayes flavour); detection derived from diagnostic-step / error-code
  coverage; severity from symptom severity. No hand-typed likelihood constants surfaced as "engineering evidence".
- **Provenance** — W3C **PROV-O** entity/activity/agent framing for honesty of lineage.

---

## Phase A — Deterministic reliability & diagnosis engine  (CLIENT-CRITICAL)
- [x] A1. Create `graph/reliability.py`: pure, testable FMEA (S/O/D, RPN, Action Priority)
      + naive-Bayes posterior functions. Fully deterministic, Neo4j-independent.
- [x] A2. Wire FMEA + posterior into `graph_rag.rank_failure_modes` (S/O/D/RPN/AP/posterior
      from graph data; rank by posterior then RPN).
- [x] A3. Replace magic-constant `_composite_confidence` (`0.65/0.35`, `max(text,0.4)`)
      with posterior-based overall confidence + separated match-quality signal.
- [x] A4. Ground `parts_predictor` scores in edge probability × failure-mode posterior
      instead of hardcoded 0.75 / 0.88 / 0.95.
- [x] A5. Unit tests `tests/test_reliability.py` (no Neo4j needed).
- [x] A6. Surface RPN / Action Priority / posterior in response + UI display.

## Phase B — Honesty of data / provenance labeling
- [x] B1. `(simulated)` labeling on PIM fixture (`simulation: true`, `generated_at`); manifest already tagged.
- [x] B2. PROV-O aligned fields in `graph/provenance.py` (activity/agent, `simulated` flag); no more implied live SAP sync.

## Phase C — Redundancy / single source of truth
- [x] C1. `synthetic_data_generator.main()` now runs a schema self-check + writes the authoritative catalog explicitly.
- [x] C2. Single authoritative source documented (`build_authoritative_catalog`); pipeline stages derive from it.
- [x] C3. Broke `graph_rag` ⇄ `diagnostic_engine` circular import (step queries moved to diagnostic_engine).

## Phase D — Architecture / domain model
- [x] D1. Typed domain models (`domain/models.py`: `DiagnosisOutcome`, `WarrantyDecision`); adopted at warranty + service boundaries.
- [x] D2. Shared `services/diagnosis_service.py`; API + UI call one path (duplicated warranty/escalation rules removed).

## Phase E — Security / robustness
- [x] E1. Fail-fast on default `neo4j_password` outside demo (settings model validator).
- [x] E2. Input validation (message min/max length, claim-status `Enum`) + global exception handler.
- [x] E3. Neo4j driver shutdown hook (FastAPI lifespan).

## Phase F — Diagrams & docs
- [x] F1. Replace `11-confidence-dilution-model.dot` with FMEA + Bayesian confidence model
      (also updated `04-graphrag-diagnosis.dot` and `07-escalation-decision.dot`; all re-rendered).
- [x] F2. Added `38-reliability-diagnosis-engine.dot` (rendered); registered in graphviz README.
- [x] F3. Updated `docs/PIPELINE-AND-MODULE-GUIDE.md` (layers + graph-driven deterministic engine section).
- [ ] F4. (nicety) Reflect `reliability.py` / `services/` / `domain/` in C4 `workspace.dsl` + diagram 23.

## Phase G — Verification
- [x] G1. Full test suite green (44 passed, incl. 11 new reliability tests) against live Neo4j;
      imports OK for `ui.app` / `api.main`; formatted response + UI escalation card verified.

Legend: [x] done · [~] in progress · [ ] pending
