# Agent entrypoint (Claude Code / Codex / Cursor)

**Always start here for implementation work.**

## Load these files first (thin always-on kit)

1. [`docs/sdd/AGENTS.md`](docs/sdd/AGENTS.md) — role, order of work, prompt pattern
2. [`docs/sdd/NEVER.md`](docs/sdd/NEVER.md) — hard-fail anti-patterns
3. [`docs/sdd/MUST.md`](docs/sdd/MUST.md) — platform non-negotiables
4. [`docs/sdd/OVERRIDES.md`](docs/sdd/OVERRIDES.md) — this project’s deltas (wins when explicit)
5. [`docs/sdd/PHASES.md`](docs/sdd/PHASES.md) — current phase + exit gates
6. [`docs/sdd/AS_BUILT.md`](docs/sdd/AS_BUILT.md) — code-true state

Then open **exactly one** task module under `docs/sdd/01`…`08` for the current work.

## Do not

- Paste the entire monorepo encyclopedia or full `docs/23-…` into every session by default.
- Invent per-product OWL/TBox files.
- Point chat at the staging graph.
- Promote without selection when work exists.

## Human / full reference

- Kit index: [`docs/sdd/README.md`](docs/sdd/README.md)
- Full SDD: [`docs/23-Spec-Driven-Development-Platform-and-Domain.md`](docs/23-Spec-Driven-Development-Platform-and-Domain.md)
- Product README: [`README.md`](README.md)
