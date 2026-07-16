# Diffusion Models for Synthetic Fault-Code Images

**Use case:** Generate claim-photo-like machine display images (error codes `5E`, `UE`, …) when historical photos are sparse — same product story as the GAN lab, with **modern diffusion** methods.

**Package:** `ml/fault_code_diffusion/`
**Adjoins:**
- GAN lab: `fault_code_gan_synthetic_images.ipynb`
- Vision MLOps: `fault_code_vision_mlops_playbook.ipynb`
- RL: `fault_code_rl_playbook.ipynb`

---

## Why diffusion for *this* product?

| Need | How diffusion helps |
|------|---------------------|
| Sparse real claim photos | Offline **data factory** for OCR / vision eval |
| Class control (`5E` vs `UE`) | **Class-conditional** generation (label embedding) |
| Stable training | Denoising MSE — fewer GAN collapse issues |
| Client GPU story | Same CUDA path as OCR/DQN (`Dockerfile.ml`) |

**Still not on the diagnose hot path:** GraphRAG remains deterministic; diffusion only synthesizes training/test images (or future augmentation services).
