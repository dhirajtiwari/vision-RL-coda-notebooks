# 04 — Platform CI

**Load when:** P7 CI gates, hermetic tests, pack contracts.

## Must implement

- [ ] Lint (e.g. ruff)
- [ ] Unit + integration pytest
- [ ] **Pack-under-TBox** tests (unknown keys / shapes fail)
- [ ] Frontend build
- [ ] Optional: image builds, secret scan, eval smoke
- [ ] Triggers on main + long-lived feature branches as needed

## Hermetic CI (paid lesson)

- Tests must **not** permanently dirty seed fixtures mid-suite.
- Multi-source pack tests should be isolatable; restore fixtures or use temp data.
- Flaky “product_count” assertions against shared seed catalogs are a known pitfall — prefer stable gates.

## As-built map (this repo)

| File | Role |
|------|------|
| `.github/workflows/ci.yml` | Main CI |
| `tests/test_multi_source_tbox_abox.py` | Multi-source / TBox discipline |
| `eval-nightly.yml` | Heavier eval when graph available |
| `cd.yml` | Deploy after CI |

## PR template questions (agents/humans)

1. Which `docs/sdd/` modules did you open?
2. Which `NEVER.md` rules apply?
3. Did you update `AS_BUILT.md` if behavior changed?
4. Fixtures still clean after local pytest?

## Exit (P7)

PR green on required checks; pack contract tests enforced.
