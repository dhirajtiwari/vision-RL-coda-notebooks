# Data Protection Impact Assessment (DPIA) — Remote Diagnostics

> Kickoff prompt §K, handbook ch11. GDPR Art. 35. This is an engineering DPIA
> skeleton — **legal counsel must review before external processing of real PII.**

## 1. Processing overview
- **Purpose:** diagnose appliance faults and determine warranty eligibility.
- **Data subjects:** customers who own registered appliances.
- **Personal data:** customer id, contact details (via CRM), asset serial numbers,
  service/claim history. No special-category data intended.
- **Lawful basis (to confirm with legal):** contract performance (warranty service)
  and/or legitimate interest.

## 2. Data flow & minimisation
- Free-text symptom description (may incidentally contain PII) → input guardrails.
- CRM/asset enrichment pulls only fields needed for warranty gating + parts binding.
- PII is **redacted** in logs, telemetry (OTel collector), and prose responses.
- Retention governed by `docs/governance/data-retention.md`.

## 3. Risks & mitigations
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| PII in logs/traces | Medium | High | `observability.redaction` + collector redact processor |
| Unauthorised access | Medium | High | Admin token now; OIDC/JWT before external exposure |
| Excessive retention | Low | Medium | Retention policy + purge job |
| Data in transit | Medium | High | `bolt+s://` TLS to Neo4j + HTTPS ingress outside demo |
| Automated decision-making | Low | Medium | Human escalation below confidence threshold (Art. 22 safeguard) |

## 4. Automated decision-making & human oversight
Warranty/diagnosis outcomes are **assistive**: low-confidence cases escalate to a
human specialist; claims/status changes require human approval (`guardrails.action`).
This provides the Art. 22 human-in-the-loop safeguard.

## 5. Residual risk & sign-off
- Residual risk: **medium** pending end-user authentication + TLS in non-demo.
- Owner: Data Protection Officer. Status: **DRAFT — awaiting legal review.**
