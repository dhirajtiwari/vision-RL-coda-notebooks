## Part 9 — Copy-paste commands (client GPU)

```bash
# From repo root
pip install -r requirements-ml.txt
# On NVIDIA hosts, install CUDA PyTorch per pytorch.org if needed

# 1) Data
python -c "from ml.fault_code_vision.pipeline import bootstrap_demo_dataset; \
print(bootstrap_demo_dataset('notebooks/fault_code_gan_artifacts/ocr_demo', n_per_code=40))"

# 2) Train (CUDA enforced)
python -m ml.fault_code_vision.train_ocr \
  --manifest notebooks/fault_code_gan_artifacts/ocr_demo/ocr_train_manifest.json \
  --epochs 30 \
  --out models/artifacts/fault-code-ocr/ocr-v1.pt \
  --require-cuda

# 3) Eval gate
python -m ml.fault_code_vision.eval_vision \
  --checkpoint models/artifacts/fault-code-ocr/ocr-v1.pt \
  --manifest notebooks/fault_code_gan_artifacts/ocr_demo/ocr_train_manifest.json \
  --split test \
  --min-accuracy 0.85 \
  --report evals/vision/reports/ocr-v1.json

# 4) Docker GPU train
docker build -f docker/Dockerfile.ml -t warrantygraph-ml:latest .
docker run --gpus all -v "$PWD":/workspace -w /workspace warrantygraph-ml:latest \
  python -m ml.fault_code_vision.train_ocr --manifest ... --require-cuda
```

### GAN lab (synthetic data factory)

Open [`fault_code_gan_synthetic_images.ipynb`](./fault_code_gan_synthetic_images.ipynb) — DCGAN/cGAN, phone augments, synthetic corpus.

### After real photos arrive

1. Add rows with `source=real`, freeze a test split.
2. Retrain reader.
3. Gate on `vision_full.real_photo_accuracy`.
4. Fill `models/finetunes/fault-code-ocr-vN.yaml`, pin `models/registry.yaml`.
5. Wire multipart API → `FaultCodeReader` → diagnose service.

---

## References

- Goodfellow et al. 2014 (GAN); Radford et al. 2016 (DCGAN); Mirza & Osindero 2014 (cGAN)
- Shorten & Khoshgoftaar 2019 (augmentation)
- This repo: `docs/sdd/09-PLATFORM-LLMOPS.md`, `docs/24-TBox-Sparse-Data-and-Enterprise-Scale-Patterns.md`
- Study module 20: synthetic data + MLOps + image ops (`study/seed_platform_modules.py`)

**Done when:** CUDA train job is reproducible, OCR is eval-gated, registry pin exists, and extracted codes boost GraphRAG the same way typed codes do today.
