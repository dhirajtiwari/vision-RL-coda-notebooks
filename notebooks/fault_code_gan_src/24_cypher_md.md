## Part 8 — Bridge extracted codes → Neo4j Cypher (this codebase)

In production diagnose flow (`graph/graph_rag.py`):

1. `match_error_codes(product_id, user_message)` runs:

```cypher
MATCH (p:Product {product_id: $product_id})-[:HAS_ERROR_CODE]->(ec:ErrorCode)
RETURN ec.error_code_id AS error_code_id, ec.code AS code, ec.description AS description
```

…then keeps rows whose `code` appears in the (OCR-filled) message.

2. `rank_failure_modes_with_error_codes` **boosts** failure modes:

```cypher
MATCH (ec:ErrorCode)-[r:INDICATES]->(fm:FailureMode)
WHERE ec.error_code_id IN $error_code_ids
RETURN fm.failure_mode_id AS failure_mode_id, sum(r.confidence) AS error_boost
```

### End-to-end simulation (no live Neo4j required)

We turn an image → code → **parameterized Cypher** + a local mini-graph that mirrors the ontology edges.
