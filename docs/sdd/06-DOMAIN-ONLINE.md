# 06 — Domain online (diagnose / UI)

**Load when:** P3 ranking/provenance, P6 UI personas, chat/explore behavior.

## Online path rules

- Diagnose and explorer **read production graph only**.
- Prefer **asset/CRM identity** binding when available over free-text product guess alone.
- Soft text mismatch with bound asset → **warn**, do not hard-block.
- Steps for top hypothesis: prefer **CONFIRMS** edges (+ limited entry prereqs), not “all steps order ≤ N”.
- Provenance should explain the **ranked** conclusion, not an arbitrary neighborhood dump.
- Partial lexical match (e.g. 60–70%) can still be correct if graph posterior is strong — check evidence id.

## Ranking (this project)

- Hybrid lexical + TF-IDF for text match
- FMEA-style severity/occurrence/detection + RPN / action priority
- Naive Bayes over graph likelihood edges
- (Optional dominance boosts as coded)

## UI personas (as-built)

Customer · Agent · Analyst · Admin

Admin owns the control-plane wizard; Customer/Agent own diagnose chat.

## As-built map

| Concern | Path |
|---------|------|
| Diagnose orchestration | `services/diagnosis_service.py` |
| GraphRAG / match | `graph/graph_rag.py` |
| Frontend | `frontend/` (Next.js) |
| Product keyword maps | present — prefer identity over expanding brittle maps long-term |

## Exit

- P3: golden phrase → ranked FM + steps + provenance
- P6: persona smoke without staging contamination
