# Fault-code vision notebooks & ML package

Two adjoining notebooks plus a production-shaped Python package for **claim display photos → fault code → GraphRAG**.

| Artifact | Purpose |
|----------|---------|
| [`fault_code_gan_synthetic_images.ipynb`](./fault_code_gan_synthetic_images.ipynb) | **Lab:** GAN theory, DCGAN/cGAN, synthetic LCD images |
| [`fault_code_vision_mlops_playbook.ipynb`](./fault_code_vision_mlops_playbook.ipynb) | **Delivery:** CUDA, train OCR, eval gates, registry, Cypher, checklist |
| [`fault_code_rl_playbook.ipynb`](./fault_code_rl_playbook.ipynb) | **RL:** bandits / Q / DQN+CUDA for next-best diagnostic steps ([README](./README-fault-code-rl.md)) |
| [`../ml/fault_code_vision/`](../ml/fault_code_vision/) | Importable train/infer/eval/Cypher package |
| [`../ml/fault_code_rl/`](../ml/fault_code_rl/) | Diagnostic MDP, bandits, Q-learning, DQN, offline IPS |
| [`../requirements-ml.txt`](../requirements-ml.txt) | Optional ML deps |
| [`../docker/Dockerfile.ml`](../docker/Dockerfile.ml) | CUDA train image |
| [`../models/registry.yaml`](../models/registry.yaml) | `fault-code-ocr` / `fault-code-gan` stubs |
| [`../evals/vision/`](../evals/vision/) | Vision eval docs + floors in `thresholds.yaml` |

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
