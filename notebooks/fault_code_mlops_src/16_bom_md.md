## Part 8 — What you need (bill of materials)

### People

| Role | Responsibility |
|------|----------------|
| ML engineer | CUDA train, OCR/GAN experiments |
| MLOps / platform | Registry, GPU jobs, monitoring, canary |
| Backend | Upload API → reader → diagnose |
| Data steward | Labels, OEM code lists, privacy |
| Domain SME | Real photo review, false-positive risk |
| Security | Upload surface, retention, threat model |

### Infrastructure

| Piece | Purpose |
|-------|---------|
| NVIDIA GPU VM or on-prem | CUDA train (T4/L4/A10+) |
| Object storage | Images, datasets, `.pt` artifacts |
| Experiment tracker | MLflow / W&B / Azure ML (optional but recommended) |
| CI | Unit tests + vision eval on PR/nightly |
| Serving | In-process Torch or Triton/TorchServe sidecar |
| Existing | FastAPI, dual Neo4j, Prometheus, evals, registry |

### Client must provide

1. Any historical display photos (even 50–200)
2. Authoritative error-code lists per product family
3. Image retention / consent policy
4. Success criteria (e.g. ≥85% real-photo code accuracy)

### Phased delivery

| Phase | Outcome |
|-------|---------|
| **0** | Charter: reader vs generator vs GraphRAG; metrics |
| **1** | CUDA env + `Dockerfile.ml` green |
| **2** | Dataset platform + real photo collection starts |
| **3** | Train reader; synthetic + real eval |
| **4** | Registry pin + CI gate + canary |
| **5** | API integration + closed-set + escalate |
| **6** | Operate: drift, retrain, dashboards, model cards |
