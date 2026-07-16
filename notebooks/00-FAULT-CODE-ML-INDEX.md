# Fault-code ML notebooks — reading order

Run from **repo root** (`diagnostic-chatbot/`) so `import ml...` works.

```bash
pip install -r requirements-ml.txt
cd /path/to/diagnostic-chatbot   # not notebooks/
```

## Recommended path (client showcase)

| # | Notebook | Audience | Runtime |
|---|----------|----------|---------|
| **1** | [`fault_code_image_generator.ipynb`](./fault_code_image_generator.ipynb) | **Start here** — enter code + machine → images | Minutes (procedural/phone instant) |
| **2** | [`fault_code_gan_synthetic_images.ipynb`](./fault_code_gan_synthetic_images.ipynb) | GAN theory + DCGAN/cGAN lab | 10–30 min train |
| **3** | [`fault_code_diffusion_playbook.ipynb`](./fault_code_diffusion_playbook.ipynb) | DDPM theory + train/sample | 20–60+ min for readable samples |
| **4** | [`fault_code_vision_mlops_playbook.ipynb`](./fault_code_vision_mlops_playbook.ipynb) | CUDA, OCR train, Cypher, registry | 15–40 min |
| **5** | [`fault_code_rl_playbook.ipynb`](./fault_code_rl_playbook.ipynb) | Bandits / Q / DQN for next-best step | 10–30 min |

## What each layer is for

```text
[Generator] procedural / GAN / diffusion  →  synthetic claim images
[Reader]    OCR CNN                       →  fault code string
[Graph]     GraphRAG Cypher               →  failure mode + steps
[Policy]    optional RL                   →  re-rank eligible steps only
```

| Layer | Production? | Notes |
|-------|-------------|--------|
| Procedural + phone | **Yes (demo data)** | Always sharp; use for OCR labels |
| GAN / diffusion | Offline factory | Need enough train epochs or samples look noisy |
| OCR | Production ML candidate | Gate on real photos |
| GraphRAG | **Core product** | Already as-built |
| RL | Optional | Never replaces GraphRAG |

## On-demand generation (no theory)

```bash
python -m ml.fault_code_vision.generate \
  --code 5E --machine washer --n 6 \
  --methods procedural,phone
```

Add `gan,diffusion` only after checkpoints exist (or accept auto-train time).

## Packages

| Package | Role |
|---------|------|
| `ml/fault_code_vision/` | Panels, generate API, cGAN, OCR, Cypher bridge |
| `ml/fault_code_diffusion/` | Conditional DDPM |
| `ml/fault_code_rl/` | Bandits, Q-learning, DQN |
| `docker/Dockerfile.ml` | Shared CUDA image |
| `requirements-ml.txt` | ML deps |

## Rebuild notebooks from cell sources

```bash
python3 notebooks/fault_code_gan_src/assemble.py
python3 notebooks/fault_code_mlops_src/assemble.py
python3 notebooks/fault_code_rl_src/assemble.py
python3 notebooks/fault_code_diffusion_src/assemble.py
```

## Known limitations (honest)

1. **Diffusion/GAN under-train → noise** — use `procedural`/`phone` for crisp demos; train 50–100 epochs on CUDA for generative quality.
2. **No Diffusers/SDXL path wired** — documented as upgrade, not implemented.
3. **No real claim photos** — all labels synthetic until client provides hold-out.
4. **OCR not FastAPI-mounted** — package + playbook only.
5. **RL is a simulator** — not wired into diagnose API.
6. **No pytest suite yet** for `ml/fault_code_*`.
