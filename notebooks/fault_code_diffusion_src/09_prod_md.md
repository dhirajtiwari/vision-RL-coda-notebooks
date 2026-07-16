## Part 5 — Production / “latest methods” upgrade path

This notebook trains a **small from-scratch DDPM** so the client sees the math run end-to-end without multi‑GB downloads.

For **photo-real** laundry-room claim images, the usual 2024–2026 stack is:

1. **Latent diffusion** (Stable Diffusion family) via [Hugging Face Diffusers](https://github.com/huggingface/diffusers)
2. **ControlNet** / IP-Adapter — lock layout to LCD panel geometry
3. **LoRA fine-tune** on real claim crops when they arrive
4. **DDIM / DPM-Solver++** — fast sampling
5. **Classifier-free guidance** — stronger adherence to code text

Optional install (not required for this notebook’s DDPM):

```bash
pip install diffusers transformers accelerate
```

### Pipeline in the product (unchanged)

```text
Diffusion (offline) → synthetic labelled images
        → OCR train/eval (vision playbook)
        → extract code → GraphRAG Cypher / INDICATES boost
```

### Hardware

| Stage | Recommendation |
|-------|----------------|
| Showcase DDPM (this nb) | MPS/CPU OK for short train; CUDA better |
| SD / LDM fine-tune | **NVIDIA CUDA**, 12–24GB+ VRAM typical |
| Shared image | `docker/Dockerfile.ml` |

### References

- Ho et al. — *Denoising Diffusion Probabilistic Models* (2020)
- Song et al. — DDIM (2021)
- Rombach et al. — *High-Resolution Image Synthesis with Latent Diffusion Models* (2022)
- Nichol & Dhariwal — improved DDPM / cosine schedule
- Diffusers docs — practical production sampling
