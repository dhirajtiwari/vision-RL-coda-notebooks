# Agent instructions (always read first)

**Audience:** Claude Code, Codex, Cursor, and any coding agent.
**Human reference (do not load by default):** `docs/23-Spec-Driven-Development-Platform-and-Domain.md` or `REFERENCE-FULL.md`.

## Role

You implement a Docker-first multi-source knowledge + query system (as-built: WarrantyGraph / remote diagnostics).
**Platform rules are fixed unless `OVERRIDES.md` changes them.**

## Context budget (lost-in-the-middle)

| Every session | Pull only when task needs it |
|---------------|------------------------------|
| This file + `NEVER.md` + `MUST.md` + `OVERRIDES.md` + `PHASES.md` + `AS_BUILT.md` | One of `01`…`08` modules |
| | Never paste full `docs/23` / encyclopedia by default |

## Before any code

1. Read `NEVER.md` and `MUST.md` completely.
2. Read `OVERRIDES.md` — if a conflict exists, **OVERRIDES wins**; record it in `AS_BUILT.md`.
3. Open `PHASES.md`; identify current phase exit gate.
4. Open `AS_BUILT.md` for code-true state (not wish-list prose).
5. Open **ONLY** the module file for this task (`01`…`09`). LLMOps → `09-PLATFORM-LLMOPS.md`. Do not invent requirements from memory.

## While coding

- Prefer the **smallest change** that satisfies the exit gate.
- Do **not** generate per-entity OWL/TBox files for new packs (ABox only under shared TBox).
- Do **not** make chat/read path use the staging graph.
- Do **not** promote without explicit selection when work exists.
- Do **not** enable `LLM_ENABLED` unless `OVERRIDES.md` / product asks; core stays deterministic.
- Do **not** paste entire `docs/llmops-handbook/` — use `09-PLATFORM-LLMOPS.md` (+ one chapter if needed).
- After implement: run the phase’s tests (and eval smoke if quality/safety touched); update `AS_BUILT.md`.
- If a bug fix creates a lasting rule → add a bullet to `NEVER.md` or `MUST.md` in the same change.

## Prompt pattern (copy into sessions)

```text
Context files: docs/sdd/AGENTS.md, NEVER.md, MUST.md, OVERRIDES.md, PHASES.md, AS_BUILT.md, <one module>
Task: <one phase-scoped outcome>
Constraints: obey NEVER.md; dual graph; production read path only.
Done when: PHASES.md exit gate true + listed tests pass + AS_BUILT.md updated.
Do not: redesign auth, add per-product OWL, or expand scope past the phase.
```

## Done definition

Exit gate checkboxes for this phase are true **AND** tests pass **AND** `AS_BUILT.md` updated.

## Repo map (this checkout only — convenience)

| Concern | Path |
|---------|------|
| Settings | `config/settings.py` |
| Infra | `docker/docker-compose.infra.yaml` |
| Pipeline control plane | `graph/enterprise_pipeline/control_plane/` |
| ABox builder | `graph/enterprise_pipeline/transformers/ontology_builder.py` |
| Shape validate | `graph/enterprise_pipeline/ontology_validate.py` |
| Diagnose | `services/diagnosis_service.py`, `graph/graph_rag.py` |
| Runtime | `runtime/*` |
| Multi-source CI | `tests/test_multi_source_tbox_abox.py` |
| LLMOps module | `docs/sdd/09-PLATFORM-LLMOPS.md` |
| Guardrails / obs / evals | `guardrails/`, `observability/`, `evals/` |
| Gateway / prompts / finops | `gateway/`, `prompts/`, `finops/` (LLM off by default) |
| Handbook (human recipe only) | `docs/llmops-handbook/` — **do not dump whole book** |
| Full SDD | `docs/23-Spec-Driven-Development-Platform-and-Domain.md` |
