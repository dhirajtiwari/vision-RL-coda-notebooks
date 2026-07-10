# Runbook — Cost Spike (LLM path)

**Alert:** `LLMCostSpike` · **Severity:** warning · **SLO:** cost
**Last tested:** _record date when rehearsed_
**Applies when:** the optional LLM path is active (`LLM_ENABLED=true`).

## Symptom
`diagnostics_llm_cost_usd_total` increasing > $2/hour, or the daily budget
circuit-breaker (`finops.budget`) tripping.

## Triage
1. Which alias/model? Break down `diagnostics_llm_tokens_total` by provider/model.
2. Runaway loop? Check for repeated calls per request_id in traces.
3. Prompt bloat? Check input token growth (a prompt/version change?).

## Mitigate
- The daily budget circuit-breaker already caps spend; to stop immediately set
  `LLM_ENABLED=false` (deterministic diagnosis continues, zero LLM cost).
- Lower `LLM_COST_BUDGET_USD_PER_DAY` or route to the cheaper `triage-classifier`
  alias while investigating.
- If a prompt change caused token bloat, roll back the prompt version.
- Multi-replica: set `REDIS_URL` so `finops.budget.DailyCostBudget` shares one
  daily counter across pods (empty URL = per-process memory only).

## Verify & close
- Cost rate returns to baseline; add a budget/eval assertion if a regression slipped through.
