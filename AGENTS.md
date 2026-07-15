# Agent entrypoint (Claude Code / Codex / Cursor)

**Always start here for implementation work.**

## Load these files first (thin always-on kit)

1. [`docs/sdd/AGENTS.md`](docs/sdd/AGENTS.md) — role, order of work, prompt pattern
2. [`docs/sdd/NEVER.md`](docs/sdd/NEVER.md) — hard-fail anti-patterns
3. [`docs/sdd/MUST.md`](docs/sdd/MUST.md) — platform non-negotiables
4. [`docs/sdd/OVERRIDES.md`](docs/sdd/OVERRIDES.md) — this project’s deltas (wins when explicit)
5. [`docs/sdd/PHASES.md`](docs/sdd/PHASES.md) — current phase + exit gates
6. [`docs/sdd/AS_BUILT.md`](docs/sdd/AS_BUILT.md) — code-true state

Then open **exactly one** task module under `docs/sdd/01`…`09` for the current work.
For LLMOps (guardrails, evals, gateway, observability): use [`docs/sdd/09-PLATFORM-LLMOPS.md`](docs/sdd/09-PLATFORM-LLMOPS.md).

## Do not

- Paste the entire monorepo encyclopedia or full `docs/23-…` into every session by default.
- Dump all of `docs/llmops-handbook/` into context — use `09-PLATFORM-LLMOPS.md` (+ one chapter if needed).
- Invent per-product OWL/TBox files.
- Point chat at the staging graph.
- Promote without selection when work exists.
- Turn on production LLM (`LLM_ENABLED`) unless `docs/sdd/OVERRIDES.md` says so — core is deterministic GraphRAG.

## Human / full reference

- Kit index: [`docs/sdd/README.md`](docs/sdd/README.md)
- Full SDD: [`docs/23-Spec-Driven-Development-Platform-and-Domain.md`](docs/23-Spec-Driven-Development-Platform-and-Domain.md)
- Patterns (TBox origin, sparse, scale): [`docs/24-TBox-Sparse-Data-and-Enterprise-Scale-Patterns.md`](docs/24-TBox-Sparse-Data-and-Enterprise-Scale-Patterns.md)
- Interview mastery (story style): [`docs/interview/Master-This-Codebase.md`](docs/interview/Master-This-Codebase.md)
- Doc reading order: [`docs/00-DOC-READING-ORDER.md`](docs/00-DOC-READING-ORDER.md)
- LLMOps handbook + playbook: [`docs/llmops-handbook/`](docs/llmops-handbook/00-index.md)
- Product README: [`README.md`](README.md)
