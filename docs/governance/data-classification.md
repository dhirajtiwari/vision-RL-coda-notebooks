# Data Classification — Remote Diagnostics

> Kickoff prompt §K, handbook ch11. Classifies every data element the system
> handles so redaction, access, and retention rules can be applied consistently.

| Data element | Class | Store | Handling |
|--------------|-------|-------|----------|
| Customer id | PII / Confidential | CRM, SQLite | Redact in logs/telemetry; access-controlled |
| Contact details (email/phone) | PII / Confidential | CRM | Never logged; redacted in responses |
| Asset serial number | PII-linked / Confidential | Neo4j, CRM | Redact in logs; used for warranty binding |
| Symptom free-text | Potentially PII / Internal | transient | Input guardrail + redaction; not persisted raw |
| Diagnosis result | Internal | Neo4j, SQLite | Provenance-tracked; retained per policy |
| Claim/case records | Confidential | SQLite | Audit columns; retention policy applies |
| Product/knowledge catalog | Public/Internal | Neo4j, JSON | Non-personal |
| ETL lineage / audit logs | Internal | JSONL | Immutable append; no raw PII |
| Model/prompt artifacts | Internal | repo | Versioned; no secrets |
| API keys / passwords | Secret | env / secret manager | Never in repo/images/logs |

## Rules by class
- **Secret:** injected at runtime only (env / cloud secret manager); never committed.
- **PII / Confidential:** redacted in logs+telemetry+responses; encrypted in transit
  (`bolt+s://`, HTTPS) outside demo; access-controlled; retention-bound.
- **Internal:** not for public exposure; standard access controls.
- **Public:** no restriction.

Redaction implementation: `observability/redaction.py` (`_SENSITIVE_KEYS` + patterns).
