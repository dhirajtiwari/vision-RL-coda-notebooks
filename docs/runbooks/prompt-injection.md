# Runbook — Prompt Injection / Jailbreak Attempt

**Source:** `guardrails.input` rejections spiking; safety eval failures.
**Severity:** warning→high · **OWASP:** LLM01/LLM07
**Last tested:** _record date when rehearsed_

## Symptom
Elevated 400s on `/diagnose` with `input rejected: prompt_injection|jailbreak|
cypher_injection`, or a probing pattern from one client.

## Triage
1. Filter structured logs for `guardrail:` rejections; group by client key.
2. Confirm the guardrail blocked it (fail-closed) — no injection reached Neo4j/LLM.
3. Assess intent: fuzzing vs targeted (repeated cypher tokens = graph attack).

## Mitigate
- Guardrails already blocked the request. For sustained abuse, rate-limit or block
  the client key (admin token / customer id / IP).
- If a novel bypass is found, add the pattern to `guardrails/input.py` AND a
  regression case to `evals/safety/injection.jsonl`, then re-run the safety suite.

## Verify & close
- Safety eval suite PASS with the new case; abuse subsides. Post-incident review
  feeds the golden/safety sets.
