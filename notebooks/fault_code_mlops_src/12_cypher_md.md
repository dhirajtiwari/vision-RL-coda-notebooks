## Part 6 — Bridge into GraphRAG / Cypher

Production path (`graph/graph_rag.py`):

1. `match_error_codes(product_id, user_message)` — codes on product whose string appears in message.
2. `rank_failure_modes_with_error_codes` — `(:ErrorCode)-[:INDICATES]->(:FailureMode)` confidence boost.

Vision should emit either:

- free-text: `Error code 5E shown on machine.` (substring match), or
- structured: `extracted_error_codes: ["5E"]` (preferred API shape when you wire multipart upload).
