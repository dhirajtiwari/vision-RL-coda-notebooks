# EvalOps — Evaluation Suites (kickoff prompt §D, handbook ch04)

The eval gate makes a non-deterministic-looking system shippable: no change
reaches production unless it clears these suites.

## Layout
```
evals/
├── run_eval.py         # gate script (exit non-zero on regression)
├── thresholds.yaml     # metric floors per suite (smoke | full)
├── golden/             # capability datasets (JSONL)
│   └── smoke.jsonl
├── safety/             # adversarial / red-team datasets (JSONL)
│   └── injection.jsonl
└── judges/             # (future) LLM-as-judge rubrics for the optional LLM path
```

## Run
```bash
# fast PR gate (safety always runs; golden runs if Neo4j is up)
python evals/run_eval.py --suite smoke

# full release gate with a JSON report
python evals/run_eval.py --suite full --report eval-report.json

# hard-fail if the graph is down (nightly job against a live Neo4j)
python evals/run_eval.py --suite full --require-graph
```

## Metrics
| Metric | Meaning | Floor source |
|--------|---------|--------------|
| `product_accuracy` | detected product == expected | thresholds.yaml |
| `confidence_pass` | meets per-case `min_confidence` | thresholds.yaml |
| `escalation_correct` | escalation flag matches expectation | thresholds.yaml |
| `safety_pass` | adversarial inputs blocked (fail-closed) | thresholds.yaml (1.0) |

## Adding cases
- Golden: append a line to `golden/*.jsonl` with `message`, `expected_product`,
  `min_confidence`, `capability`, `risk`.
- Safety: append to `safety/*.jsonl` with `message`, `expect_block`, `category`.
- Every production incident should add a regression case here (ch15 feedback loop).

## Judges (future / LLM path)
When the optional LLM rewriter is activated, add versioned judge rubrics under
`judges/` and gate on faithfulness/groundedness with tolerance bands.
