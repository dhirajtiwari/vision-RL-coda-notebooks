# Data Retention Policy — Remote Diagnostics

> Kickoff prompt §K, handbook ch11. GDPR storage-limitation principle (Art. 5(1)(e)).
> **Confirm periods with legal/DPO before production.**

| Data | Default retention | Basis | Purge mechanism |
|------|-------------------|-------|-----------------|
| Symptom free-text | Not persisted raw (transient) | Minimisation | n/a |
| Diagnosis results | 24 months | Warranty/service history | Scheduled purge job |
| Claim/case records | 6 years | Financial/warranty record-keeping | Archived then purged |
| CRM enrichment cache | Session only | Minimisation | Evicted after request |
| ETL lineage / audit logs | 13 months | Operational audit | Rotated |
| Traces/metrics | 30 days | Ops troubleshooting | Backend retention config |
| Structured logs | 30 days | Ops/security | Log backend rotation |

## Subject rights (GDPR)
- **Erasure (Art. 17):** deletion of a customer's diagnosis/claim records supported
  via the SQLite operational store + graph tombstoning; document the procedure before
  handling real requests.
- **Access/Portability (Art. 15/20):** export a subject's records from CRM + SQLite.

## Implementation status
- Purge/erasure jobs are **not yet implemented** — tracked as a governance gap
  (owner: Data Gov). Retention windows above are the target policy.
