# Runbook — Stale Knowledge Graph (freshness)

**Alert:** `EscalationSurge` · **Severity:** warning · **SLO:** quality/freshness
**Last tested:** _record date when rehearsed_

## Symptom
High escalation ratio; diagnoses returning "insufficient knowledge"; provenance
trails pointing at old source batches.

## Triage
1. `GET /lineage/batches` — when was the last successful ETL batch? Compare to the
   expected ingestion cadence (see `ingestion/schedule.md` if present).
2. `GET /integrations/status` — are CRM/PIM/FSM/Claims connectors healthy?
3. Check the ETL CronJob (k8s) / local ETL run logs for errors.

## Mitigate
- Trigger a fresh ETL run (admin pipeline): dry-run → validate (smoke) → review → promote.
- If a connector is down, fixture fallback keeps the demo running but flags staleness.
- If a batch is corrupt, re-run the previous known-good batch.

## Verify & close
- New batch appears in `/lineage/batches` with status=ok; escalation ratio normalises.
