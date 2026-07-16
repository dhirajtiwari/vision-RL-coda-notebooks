## Part 1 — How it works end-to-end

### Training time (offline, prefer NVIDIA CUDA)

```text
Real claim photos (when any) ──┐
Procedural LCD seeds ──────────┼──► versioned dataset (manifest + object store)
Classical augments ────────────┤
GAN/diffusion synthetic ───────┘
         │
         ▼
   Train OCR / closed-set classifier (CUDA)
         │
         ▼
   Eval gates (synthetic hold-out + REAL hold-out)
         │
         ▼
   models/registry.yaml pin ──► deploy canary ──► full
```

### Runtime (online — usually CPU; GPU only if QPS needs it)

```text
Customer photo
  → authz + malware scan + size limits
  → FaultCodeReader (pinned artifact)
  → closed-set ∩ product HAS_ERROR_CODE
  → low conf? escalate / retake
  → else user_message or structured error_codes[]
  → graph_rag.match_error_codes + INDICATES boost
  → CONFIRMS steps + parts + provenance (incl. model_version)
```

### Design rule (ADR 0001 aligned)

- **Deterministic core** stays GraphRAG — vision is an **input normalizer**, not a free-form diagnostic LLM.
- Synthetic data is labelled `source=synthetic` and never silent “historical claim truth.”
- Promote OCR only when **real-photo** floors pass (see `evals/thresholds.yaml` → `vision_full.real_photo_accuracy`).
