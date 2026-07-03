# Progressive Delivery (kickoff prompt §N, handbook ch14)

Canary delivery with **automated metric analysis + rollback**, keyed to
LLM/diagnosis-specific metrics — not just infra health. Two controllers are
scaffolded so you can pick one; keep the other for reference.

```
deploy/
├── rollouts/
│   ├── argo-rollout.yaml      # Argo Rollouts: Rollout + AnalysisTemplate
│   └── flagger-canary.yaml    # Flagger: Canary + MetricTemplate
├── policy/
│   └── verify-images.yaml     # Kyverno: only run cosign-signed images (§M)
└── helm/                      # optional Helm packaging (project uses Kustomize)
```

## Canary gate metrics (baseline-relative)
Both configs analyse:
- **error rate** — `diagnostics_requests_total{status=~"5.."}` ratio (infra).
- **latency p95** — `diagnostics_request_latency_seconds` (infra).
- **diagnosis confidence** — `diagnostics_diagnosis_confidence` median (quality).

A breach on any metric **auto-rolls-back**. This protects against a bad graph/ETL
promotion or (later) a bad prompt/model silently degrading diagnosis quality.

## Rollback decision tree (§N)
1. **Quality drop only** → roll back prompt/model (alias flip in `models/registry.yaml`)
   or re-run previous ETL batch. No image redeploy.
2. **Errors/latency** → roll back the image (last known-good digest).
3. **Cost spike** (LLM path) → circuit-breaker + disable LLM (`LLM_ENABLED=false`).

Prefer **config-level** rollback (alias/prompt/flag) over image redeploy.

## Choosing a controller
- **Argo Rollouts** — explicit `steps:` with pause/analysis; good for staged %.
- **Flagger** — declarative `analysis:` loop with webhooks; good with a mesh/ingress.
Set one as active in your Kustomize overlay; both read the same Prometheus metrics.
