# OWASP Top 10 for LLM Applications (2025) — Control Mapping

> Kickoff prompt §J, handbook ch10. Every risk maps to a concrete control, an
> owner, and (where applicable) a red-team case in `evals/safety/`.
>
> **Context:** the core diagnosis engine is **deterministic** (Neo4j + FMEA/Bayes),
> so several LLM-specific risks are *low/inactive* today but are pre-controlled so
> activating the optional LLM path (OpenAI / Azure AI Foundry) is safe by default.

| ID | Risk | Applicability | Control | Owner | Red-team |
|----|------|---------------|---------|-------|----------|
| **LLM01** | Prompt Injection | Active (free-text input); High if LLM enabled | `guardrails.input` (injection/jailbreak regex) + retrieved content treated as data; output validation when LLM on | Platform | injection.jsonl |
| **LLM02** | Sensitive Information Disclosure | Active | `observability.redaction` in logs/telemetry/responses; output guardrail; secrets via env/secret-manager | Security | — |
| **LLM03** | Supply Chain | Active | Pinned deps + `pip-audit` in CI; SBOM + image signing (ch13); pinned model versions in `models/registry.yaml` | Platform | — |
| **LLM04** | Data & Model Poisoning | Active (graph ingestion) | Provenance (`graph/provenance.py`) + ETL approval gate + smoke validation before promote | Data Gov | — |
| **LLM05** | Improper Output Handling | Active | Never pass output to SQL/shell/HTML unescaped; Pydantic response schema; output length cap | Platform | — |
| **LLM06** | Excessive Agency | Inactive (no tool-calling) | `guardrails.action` default-deny allowlist + HITL for claims/status changes | Platform | — |
| **LLM07** | System Prompt Leakage | Inactive (LLM path) | Prompts are server-side artifacts (`prompts/`); injection guardrail blocks "reveal prompt" | Platform | injection.jsonl |
| **LLM08** | Vector/Embedding Weaknesses | Low (graph retrieval, no vectors) | ACL/metadata filters at query time; if embeddings added, pin model + re-embed migration | Data Gov | — |
| **LLM09** | Misinformation | Active | Grounded provenance trail on every diagnosis; confidence gate → human escalation; fact-locked rewriter prompt | Product | golden set |
| **LLM10** | Unbounded Consumption | Active | Rate limiter (§E) + FinOps daily budget circuit-breaker (`finops.budget`) + agent step caps | Platform | — |

## Verification
- Guardrail behaviour is asserted by `tests/test_guardrails.py` and the safety eval suite.
- Supply-chain controls run in `.github/workflows/ci.yml` (pip-audit + SBOM + sign).
- Update this table whenever a control or owner changes; a risk with no owner is unowned risk.
