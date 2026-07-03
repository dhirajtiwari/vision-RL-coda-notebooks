# Runbook — Latency Regression

**Alert:** `DiagnoseLatencyP95High` · **Severity:** warning · **SLO:** latency-p95 (< 2s)
**Last tested:** _record date when rehearsed_

## Triage
1. Trace a slow `request_id` (OTel) — which span dominates: Neo4j query, connector
   HTTP, or (if active) the LLM call?
2. Check Neo4j health/load; check connector latency in `/integrations/status`.

## Mitigate
- **Neo4j slow:** check query plans / indexes; scale the StatefulSet resources.
- **Connector slow:** enable fixture fallback to shed latency; open a ticket upstream.
- **LLM slow (optional path):** switch to the faster/cheaper alias or disable LLM.

## Verify & close
- p95 back under 2s; add a perf guard if a query regressed.
