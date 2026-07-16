# Vision eval suite (fault-code OCR)

**Status:** scaffold for client CUDA/MLOps delivery.
**Promotion rule:** do **not** promote an OCR model on synthetic-only scores. Require a real-photo hold-out once client images exist.

## Run

```bash
# 1) Bootstrap seed dataset + train (CPU/MPS/CUDA)
python -c "from ml.fault_code_vision.pipeline import bootstrap_demo_dataset; print(bootstrap_demo_dataset('notebooks/fault_code_gan_artifacts/ocr_demo'))"

python -m ml.fault_code_vision.train_ocr \
  --manifest notebooks/fault_code_gan_artifacts/ocr_demo/ocr_train_manifest.json \
  --epochs 10 \
  --out notebooks/fault_code_gan_artifacts/checkpoints/ocr.pt

# 2) Eval gate
python -m ml.fault_code_vision.eval_vision \
  --checkpoint notebooks/fault_code_gan_artifacts/checkpoints/ocr.pt \
  --manifest notebooks/fault_code_gan_artifacts/ocr_demo/ocr_train_manifest.json \
  --split test \
  --min-accuracy 0.80 \
  --report notebooks/fault_code_gan_artifacts/ocr_eval_report.json
```

## Floors

See `evals/thresholds.yaml` → `vision_smoke` / `vision_full`.

## Related

- Playbook notebook: `notebooks/fault_code_vision_mlops_playbook.ipynb`
- GAN lab notebook: `notebooks/fault_code_gan_synthetic_images.ipynb`
- Package: `ml/fault_code_vision/`
