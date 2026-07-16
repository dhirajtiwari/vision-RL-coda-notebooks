# Fault-Code Vision — CUDA, Training & MLOps Playbook

**Adjoins:** [`fault_code_gan_synthetic_images.ipynb`](./fault_code_gan_synthetic_images.ipynb) (lab: GAN theory + synthetic displays)
**Package:** `ml/fault_code_vision/`
**Domain:** WarrantyGraph — claim photo of machine fault code → OCR → Neo4j GraphRAG

---

## What this notebook is

The GAN notebook proves **image synthesis**. This playbook answers the client question:

> *If we need CUDA, trained models, and full MLOps — what do we build, what do we need, and how does it work?*

It is **executable**: environment checks, dataset bootstrap, OCR train/eval, Cypher bridge, registry/eval floors, and a delivery checklist — all in-repo.

---

## Mental model (do not confuse these three systems)

| System | Job | When | Production? |
|--------|-----|------|-------------|
| **A. Generator (GAN/cGAN/diffusion)** | Manufacture labelled display photos | Offline batch | Data factory only |
| **B. Reader (OCR / CNN / TrOCR)** | Pixels → fault code string | Online on claim | **Yes — production ML** |
| **C. GraphRAG diagnose** | Code → FM → steps/parts (Neo4j) | Online | **Yes — deterministic core (already built)** |

> We do **not** put a GAN on the live claim path. We train a **reader**, gate it, pin it in the registry, and feed `match_error_codes` / `INDICATES` boosts.
