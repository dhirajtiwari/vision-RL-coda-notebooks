# Fault-code vision notebooks & ML package

**Full index / reading order:** [`00-FAULT-CODE-ML-INDEX.md`](./00-FAULT-CODE-ML-INDEX.md)

Claim display photos → fault code → GraphRAG (+ optional RL).

| Artifact | Purpose |
|----------|---------|
| [`fault_code_image_generator.ipynb`](./fault_code_image_generator.ipynb) | **Start here:** code + machine → image set (procedural/phone/gan/diffusion) |
| [`fault_code_gan_synthetic_images.ipynb`](./fault_code_gan_synthetic_images.ipynb) | **Lab:** GAN theory + DCGAN/cGAN |
| [`fault_code_diffusion_playbook.ipynb`](./fault_code_diffusion_playbook.ipynb) | **Diffusion:** DDPM theory + train/sample |
| [`fault_code_vision_mlops_playbook.ipynb`](./fault_code_vision_mlops_playbook.ipynb) | **Delivery:** CUDA, OCR, Cypher, registry |
| [`fault_code_rl_playbook.ipynb`](./fault_code_rl_playbook.ipynb) | **RL:** bandits / Q / DQN ([README](./README-fault-code-rl.md)) |
| [`../ml/fault_code_vision/`](../ml/fault_code_vision/) | Panels, `generate` API, cGAN, OCR, Cypher |
| [`../ml/fault_code_diffusion/`](../ml/fault_code_diffusion/) | Conditional DDPM |
| [`../ml/fault_code_rl/`](../ml/fault_code_rl/) | Diagnostic MDP / bandits / DQN |
| [`../requirements-ml.txt`](../requirements-ml.txt) | Optional ML deps |
| [`../docker/Dockerfile.ml`](../docker/Dockerfile.ml) | CUDA train image |
| [`../models/registry.yaml`](../models/registry.yaml) | Vision + RL registry stubs |
| [`../evals/vision/`](../evals/vision/), [`../evals/rl/`](../evals/rl/) | Eval floors |


## Quick start

```bash
# from repo root
pip install -r requirements-ml.txt

# Playbook path: bootstrap → train OCR → eval
python -c "from ml.fault_code_vision.pipeline import bootstrap_demo_dataset; print(bootstrap_demo_dataset('notebooks/fault_code_gan_artifacts/ocr_demo'))"

python -m ml.fault_code_vision.train_ocr \
  --manifest notebooks/fault_code_gan_artifacts/ocr_demo/ocr_train_manifest.json \
  --epochs 10 \
  --out notebooks/fault_code_gan_artifacts/checkpoints/ocr.pt

python -m ml.fault_code_vision.eval_vision \
  --checkpoint notebooks/fault_code_gan_artifacts/checkpoints/ocr.pt \
  --manifest notebooks/fault_code_gan_artifacts/ocr_demo/ocr_train_manifest.json \
  --split test --min-accuracy 0.80
```

Open notebooks:

```bash
open notebooks/fault_code_vision_mlops_playbook.ipynb
open notebooks/fault_code_gan_synthetic_images.ipynb
```

## Rebuild notebooks from sources

```bash
python3 notebooks/fault_code_gan_src/assemble.py
python3 notebooks/fault_code_mlops_src/assemble.py
```

## Architecture reminder

- **GAN** = offline data factory (sparse historical photos).
- **OCR CNN** = production reader (pixels → code).
- **GraphRAG** = existing Neo4j diagnose (`match_error_codes` / `INDICATES`).
