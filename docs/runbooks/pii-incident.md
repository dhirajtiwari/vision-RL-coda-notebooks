# Runbook — PII Incident (GDPR)

**Severity:** high/critical · **Regulatory:** GDPR (72h breach-notification clock)
**Last tested:** _record date when rehearsed_

## Symptom
PII (customer id, serial, email, phone) observed in logs, telemetry, responses,
or an unauthorised access report.

## Immediate actions (first hour)
1. **Contain:** confirm `ENABLE_PII_REDACTION=true`; if a leak path is found,
   disable the affected endpoint/exporter.
2. **Scope:** what fields, how many subjects, which store (logs/traces/DB/response)?
   Filter by `request_id` to bound exposure.
3. **Preserve evidence:** snapshot affected logs before rotation.

## Mitigate
- Patch the leak (add pattern to `observability/redaction.py`; redaction runs in
  logs, the OTel collector `attributes/redact` processor, and output guardrails).
- Purge leaked data from downstream stores per retention policy
  (see `docs/governance/data-retention.md`).

## Notify & record (GDPR)
- Engage the Data Protection Officer / legal. Assess Art. 33/34 notification duty
  (**72h** to supervisory authority if risk to individuals).
- Record in the incident register; update the DPIA (`docs/governance/dpia.md`).

## Verify & close
- Redaction verified by test; add a regression test asserting the field is masked.
