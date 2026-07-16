## Part 8b — How this plugs into the diagnose API

Conceptual integration (does not change production code in this notebook):

```text
POST /diagnose  (or future POST /claims/{id}/attachments)
  multipart: image + product_id / asset_id
       |
       v
  crop panel ROI -> extract_code_from_image()
       |
       v
  user_message += " Error code {code} shown on machine."
       |
       v
  services/diagnosis_service.py -> graph_rag.match_error_codes()
       |
       v
  rank_failure_modes_with_error_codes()  # INDICATES confidence boost
       |
       v
  CONFIRMS diagnostic steps + parts + historical resolutions
```

Synthetic images from Part 6 populate:

| Artifact | Use |
|----------|-----|
| `synthetic_corpus_manifest.json` | Train / fine-tune OCR or vision model |
| `ocr_eval_report.json` | Efficacy baseline (synthetic proxy) |
| `checkpoints/cgan.pt` | Regenerate more images on demand for rare codes |

### Production hardening checklist

1. **Real-photo hold-out gate** before promoting OCR models.
2. **PII / scene safety** — claim photos may include faces, rooms; redact if stored.
3. **Closed-set preference** — only accept codes in product's `HAS_ERROR_CODE` list (prevents OCR hallucinations from inventing edges).
4. **Confidence + human escalate** when OCR confidence low (matches existing `should_escalate` patterns).
5. **Lineage** — tag synthetic samples so they never silently mix into "historical claim photo" truth tables without label.
