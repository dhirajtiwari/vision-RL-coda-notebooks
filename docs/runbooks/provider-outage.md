# Runbook — Provider / Dependency Outage

**Alert:** `DiagnoseHighErrorRate` · **Severity:** critical · **SLO:** availability
**Last tested:** _record date when rehearsed_

## Symptom
`/diagnose` returning 5xx; `/health` shows `neo4j: false` or a connector failing.

## Triage (fast)
1. `curl /health` — which dependency is down (Neo4j vs connectors)?
2. Check container/pod status and logs (structured JSON logs, filter by `request_id`).
3. Confirm scope: all requests or a subset (one tenant/product)?

## Mitigate
- **Neo4j down:** restart the Neo4j container/StatefulSet; verify `bolt` reachable.
  The graph_rag layer falls back to the static OEM catalog for product detection,
  but full diagnosis needs Neo4j — restore it first.
- **Connector (CRM/PIM/FSM/Claims) down:** `allow_fixture_fallback` keeps the demo
  serving from local fixtures; flag degraded enrichment.
- **LLM provider down (optional path):** the gateway falls back to the alias's
  configured fallback provider (OpenAI ↔ Azure Foundry); if both down, disable the
  LLM path (`LLM_ENABLED=false`) — deterministic diagnosis continues.

## Verify & close
- Error rate returns below 5%; `/health` all-green. File a blameless post-incident review.
