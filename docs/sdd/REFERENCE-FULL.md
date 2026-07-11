# REFERENCE-FULL (humans / planning only)

This is **not** an always-on agent context file.

**Canonical long-form SDD** (platform vs domain, as-built §1, gaps §6, agent packaging §0.4):

→ [`../23-Spec-Driven-Development-Platform-and-Domain.md`](../23-Spec-Driven-Development-Platform-and-Domain.md)

## How to use

| Audience | Practice |
|----------|----------|
| Human architect | Read end-to-end once; then maintain modular files in this directory |
| Claude Code / Codex | Load `AGENTS` + `NEVER` + `MUST` + `OVERRIDES` + `PHASES` + `AS_BUILT` + **one** `01`…`08` module |
| Planning agent | May open `08-GAPS.md` or §6 of the full doc when choosing roadmap |

If you need a single portable dump for offline human review, copy `docs/23-…` as `REFERENCE-FULL.md` content; prefer linking to keep one source of truth.
