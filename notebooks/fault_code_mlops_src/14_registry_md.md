## Part 7 — MLOps control plane (this repo)

### Lifecycle (memorize)

```text
Data → Train → Eval gates → Registry pin → Deploy (flag/alias)
  → Monitor quality/cost/latency → Rollback or retrain
```

### Artifacts already stubbed

| Artifact | Role |
|----------|------|
| `models/registry.yaml` → `fault-code-ocr` / `fault-code-gan` | Aliases (`status: inactive` until gated) |
| `models/finetunes/fault-code-ocr.example.yaml` | Provenance template |
| `evals/thresholds.yaml` → `vision_smoke` / `vision_full` | Floors |
| `evals/vision/` | Suite docs + schema examples |
| `docker/Dockerfile.ml` | CUDA train image |
| `requirements-ml.txt` | ML deps separated from core API |
| `finops/budget.py` | Extend with $/1k images + GPU-hours |
| `observability/` + Prometheus | Add `ocr_*` series at API wire-up |
| `guardrails/` | Rate limit, size caps, closed-set on upload |

### Rollback

Flip registry `artifact` / `status` to previous pin — same pattern as LLM alias rollback. No need to redeploy the graph.
