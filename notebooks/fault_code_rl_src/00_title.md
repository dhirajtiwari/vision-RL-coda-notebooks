# Reinforcement Learning for Warranty Diagnostics — Theory, Math & CUDA Playbook

**Domain:** WarrantyGraph / remote diagnosis (GraphRAG + optional vision OCR)
**Package:** `ml/fault_code_rl/`
**Adjoins:**
- [`fault_code_gan_synthetic_images.ipynb`](./fault_code_gan_synthetic_images.ipynb) — synthetic fault-code images
- [`fault_code_vision_mlops_playbook.ipynb`](./fault_code_vision_mlops_playbook.ipynb) — CUDA vision MLOps

---

## Client question this notebook answers

> *If reinforcement learning is required, what kind, with what mathematics, how does it work with GraphRAG, and how do we train on CUDA like the vision stack?*

### Honest product stance

| Layer | Role of RL |
|-------|------------|
| **GraphRAG (Neo4j)** | **Primary reasoner** — FailureMode ranking, CONFIRMS steps, provenance (keep) |
| **Vision OCR** | Input normalizer: photo → error code |
| **RL (optional)** | **Decision policy** on top: next-best step, escalation cost trade-offs, offline improvement from claim outcomes |

**Do not** replace deterministic graph diagnosis with unconstrained RL.
**Do** use RL to re-rank **graph-eligible** actions under a logged reward (resolve / cost / reopen).
