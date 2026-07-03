# Fine-tune provenance records (kickoff prompt §G §7.7)

Place one YAML per fine-tuned model here. Each record pins:

- `base_model` (pinned version)
- `training_data` (dataset id + content hash + governance approval)
- `method` (SFT / LoRA / QLoRA / DPO)
- `eval_baseline` (the eval run that gated promotion)
- `approved_by` / `date`

The core diagnosis system is deterministic and currently ships **no** fine-tuned
models — this directory is a landing zone for when a custom model is introduced.
See handbook ch07 §7.7 for the record schema.
