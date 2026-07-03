# Changelog — `diagnosis-rewriter`

All notable changes to this prompt are recorded here. Prompts are versioned
artifacts (kickoff prompt §B). A version bump = a new `vN.yaml` + an entry below
+ a passing eval run.

## v1 — initial
- Customer-facing rewriter for the deterministic diagnosis result.
- Fact-locked: may only rephrase provided grounded fields, never invent.
- Rollback path: set `LLM_ENABLED=false` (deterministic response) or point the
  `diagnosis-rewriter` alias at the previous version.
