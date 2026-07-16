## Table of contents

| Part | Content |
|------|---------|
| **0** | Repo map & imports |
| **1** | How the full system works (train vs runtime) |
| **2** | CUDA / device readiness |
| **3** | Data strategy & manifest schema |
| **4** | Bootstrap seeds + train production **reader** (OCR CNN) |
| **5** | Eval gates & promotion floors |
| **6** | Cypher / GraphRAG bridge + API payload |
| **7** | Model registry, FinOps, observability |
| **8** | Client bill of materials & phased plan |
| **9** | Checklist + next commands |

### Authoritative hooks in this monorepo

| Concern | Path |
|---------|------|
| LLMOps module | `docs/sdd/09-PLATFORM-LLMOPS.md` |
| Model registry | `models/registry.yaml` (`fault-code-ocr`, `fault-code-gan` stubs) |
| Finetune record example | `models/finetunes/fault-code-ocr.example.yaml` |
| Vision eval | `evals/vision/`, floors in `evals/thresholds.yaml` |
| ML package | `ml/fault_code_vision/` |
| GPU Dockerfile | `docker/Dockerfile.ml` |
| ML deps | `requirements-ml.txt` |
| Diagnose Cypher | `graph/graph_rag.py` → `match_error_codes`, `rank_failure_modes_with_error_codes` |
