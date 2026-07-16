## Part 5 — Eval gates & promotion

| Suite | Floor (see `evals/thresholds.yaml`) | Use |
|-------|-------------------------------------|-----|
| `vision_smoke` | `code_accuracy` ≥ 0.80 | Dev / PR proxy on synthetic |
| `vision_full` | synthetic ≥ 0.90; **`real_photo_accuracy` ≥ 0.85** | Production pin |

**Never** lower floors to go green. **Never** promote on synthetic-only when real photos exist.

```bash
python -m ml.fault_code_vision.eval_vision \
  --checkpoint .../ocr.pt \
  --manifest .../ocr_train_manifest.json \
  --split test \
  --min-accuracy 0.80
```
