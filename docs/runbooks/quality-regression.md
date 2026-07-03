# Runbook — Quality Regression (diagnosis confidence drop)

**Alert:** `DiagnosisConfidenceDrop` · **Severity:** warning · **SLO:** quality
**Last tested:** _record date when rehearsed_

## Symptom
Median diagnosis confidence < 0.40 over 30m, or `EscalationSurge` firing.

## Likely causes
1. Stale/incomplete graph after an ETL promotion (missing symptoms/failure modes).
2. A bad prompt/model change (only if the optional LLM path is active).
3. Input distribution shift (new product line, new phrasing).

## Triage (5 min)
1. Check `/health` and `/integrations/status` — is Neo4j up and connectors green?
2. `GET /lineage/batches` — did an ETL batch land right before the drop?
3. Run the eval gate against live graph:
   ```bash
   python evals/run_eval.py --suite full --require-graph --report eval-report.json
   ```

## Mitigate
- **If a recent ETL batch caused it:** re-run the previous known-good batch
  (staging promotion supports rollback) and re-validate.
- **If a prompt/model change caused it (LLM path):** flip `LLM_ENABLED=false`
  (deterministic response) or point the `diagnosis-rewriter` alias at the prior
  version in `models/registry.yaml`. No code deploy needed.
- **If input shift:** add the new cases to `evals/golden/` and tune retrieval.

## Verify & close
- Median confidence recovers above floor; eval gate PASS.
- Add a regression case to `evals/golden/` from the incident (feedback loop).
