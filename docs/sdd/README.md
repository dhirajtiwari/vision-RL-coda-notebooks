# Spec-Driven Development kit (agent-native)

Thin, progressive files so Claude Code / Codex / humans avoid **lost-in-the-middle** on a single giant doc.

## Always load (every agent session)

| File | Purpose |
|------|---------|
| [`AGENTS.md`](./AGENTS.md) | Role, order of work, prompt pattern |
| [`NEVER.md`](./NEVER.md) | Hard fail anti-patterns |
| [`MUST.md`](./MUST.md) | Platform non-negotiables |
| [`OVERRIDES.md`](./OVERRIDES.md) | **This project** deltas (wins when explicit) |
| [`PHASES.md`](./PHASES.md) | Phase table + exit gates |
| [`AS_BUILT.md`](./AS_BUILT.md) | Code-true state (update after each phase) |

## Pull on demand (one module per task)

| File | When |
|------|------|
| [`01-PLATFORM-DOCKER.md`](./01-PLATFORM-DOCKER.md) | Infra / compose / health |
| [`02-PLATFORM-INGEST.md`](./02-PLATFORM-INGEST.md) | Pipelines / promote / selection |
| [`03-PLATFORM-RUNTIME.md`](./03-PLATFORM-RUNTIME.md) | Cache / parallel / rate / admission |
| [`04-PLATFORM-CI.md`](./04-PLATFORM-CI.md) | CI / hermetic tests |
| [`05-DOMAIN-ONTOLOGY.md`](./05-DOMAIN-ONTOLOGY.md) | TBox / ABox / packs |
| [`06-DOMAIN-ONLINE.md`](./06-DOMAIN-ONLINE.md) | Diagnose / UI |
| [`07-ACCEPTANCE.md`](./07-ACCEPTANCE.md) | Parity checklists |
| [`08-GAPS.md`](./08-GAPS.md) | Roadmap beyond parity (planning) |

## Human full reference

- Canonical long form: [`../23-Spec-Driven-Development-Platform-and-Domain.md`](../23-Spec-Driven-Development-Platform-and-Domain.md)
- Pointer: [`REFERENCE-FULL.md`](./REFERENCE-FULL.md)

**Agents:** do **not** attach the full reference every turn.

## Repo entrypoint for tools

Root [`../../AGENTS.md`](../../AGENTS.md) points here so Claude Code / Codex discover the kit.

## Greenfield fork

1. Copy this entire `docs/sdd/` directory.
2. Rewrite `OVERRIDES.md` and domain modules (`05`, `06`).
3. Reset `AS_BUILT.md` and phase checkboxes.
4. Keep `NEVER.md` / `MUST.md` unless you have an explicit reason (record in OVERRIDES).
