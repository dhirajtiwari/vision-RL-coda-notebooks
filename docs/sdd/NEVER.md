# NEVER (hard fail if agent does these)

Keep this file short. New paid lessons → add a bullet **the same week**.

## Ontology / knowledge

- NEVER invent a new ontology/schema language (OWL/TTL) per product/device pack — ABox only under shared TBox.
- NEVER treat “sources on disk” as “schema built” — sources feed instances; TBox lives in the platform module.
- NEVER auto-merge unknown pack keys into TBox without human governance (`tbox_extension` candidates only).
- NEVER validate only after graph load — shape-check ABox **before** materialize/promote.
- NEVER present full TBox dump as “the change set” — highlight NEW ABox / entity delta.

## Dual graph / promote / selection

- NEVER point online query/chat/explore at the **staging** graph as production.
- NEVER promote the whole fleet when the operator selected a subset.
- NEVER treat empty selection as “promote everything” when actionable work exists — fail closed.
- NEVER treat staging success as “chat ready” — chat reads production only.
- NEVER equate fleet-wide UPDATE noise with “this batch failed” after a successful promote — split fleet vs selection status.
- NEVER force UPDATE on bulletin-only metadata without real ABox growth.
- NEVER leave the admin wizard stuck “complete” with no path to next work — support session reset-for-next-cycle.

## Diagnosis / ranking / UX

- NEVER hard-block diagnose solely on soft text mismatch when an asset is already bound — warn, still diagnose bound product.
- NEVER return “all steps with order ≤ N” as the procedure — prefer CONFIRMS(top hypothesis) (+ limited entry prereqs).
- NEVER treat 60–70% lexical match as “not in KG” without checking matched evidence id + posterior.
- NEVER match product codes as bare substrings of English words without word-boundary care.

## Data honesty / security / process

- NEVER claim live SoR integration (SAP/Salesforce/etc.) when only fixtures/mocks run — label simulated.
- NEVER ship open Admin promote on a public network and call it enterprise-ready.
- NEVER cache query answers by raw message alone — must include identity + catalog/version scope.
- NEVER bury a new hard constraint only in a long essay — add a NEVER/MUST bullet.
- NEVER skip updating `AS_BUILT.md` after a phase.
- NEVER rewrite seed fixtures mid-suite without restore — keep CI hermetic.
- NEVER depend on another machine’s monorepo docs to rebuild — SDD kit must travel alone.

## LLMOps (handbook / playbook — paid lessons)

- NEVER put security controls “only in the prompt” — enforce in `guardrails/` / redaction / infra and **test** them.
- NEVER embed prompts or model IDs as unversioned string literals — use `prompts/` + `models/registry.yaml`.
- NEVER pin models to `latest` — registry must pin versions; silent drift is a defect.
- NEVER ship without an eval + safety gate (`evals/run_eval.py` + thresholds) when changing diagnose quality/safety.
- NEVER loosen `thresholds.yaml` floors to make CI green — fix the regression.
- NEVER claim EU AI Act / NIST / GDPR “certified” without legal + implemented controls — mark drafts, list residual risks.
- NEVER log raw PII bodies “for debugging” — redaction on; see runbook `pii-incident`.
- NEVER force heavy OTEL/LLM stacks into base install as required deps — keep opt-in where as-built does.
- NEVER activate production LLM path without FinOps budget breaker + metering wired.
- NEVER dump the entire `docs/llmops-handbook/` into agent context — load `09-PLATFORM-LLMOPS.md` + one chapter if needed.
- NEVER treat progressive-delivery / Terraform scaffolds as “live multi-cluster prod” without evidence.
