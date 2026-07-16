## Part 4 — Train the production reader (not the GAN)

The **GAN** (other notebook) augments sparse data.
The **reader** is what production calls.

Package entrypoint:

```bash
python -m ml.fault_code_vision.train_ocr \
  --manifest <manifest.json> \
  --epochs 20 \
  --out models/artifacts/fault-code-ocr/ocr-v1.pt \
  --require-cuda   # on client GPU
```

Below we train a short run in-process for the playbook (CPU/MPS/CUDA).
