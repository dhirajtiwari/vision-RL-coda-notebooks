# GAN-Based Synthetic Device Fault-Code Image Generation

**Domain:** Appliance warranty remote diagnostics (WarrantyGraph)
**Goal:** Synthetically generate *claim-photo-like* images of machine-displayed fault/error codes so we can train and evaluate OCR → graph lookup when historical claim photos are sparse or missing.
**Stack:** PyTorch DCGAN + Conditional GAN (cGAN), PIL seed renderer, Neo4j Cypher templates aligned with this repo.

---

## Why this exists (client problem)

| Reality | Impact |
|---------|--------|
| Customers photograph the **error code on the appliance display** when filing a claim | Our app must **read** that code (OCR / vision) |
| Extracted code maps to `ErrorCode` nodes and boosts failure-mode ranking | GraphRAG Cypher: `(:ErrorCode)-[:INDICATES]->(:FailureMode)` |
| Historical resolution cases often **lack** those photos | Sparse / zero real images → cannot measure OCR accuracy or end-to-end efficacy |
| Need synthetic images that **mimic** LCD/LED fault displays under phone-camera conditions | Train & stress-test extraction **before** real claim volume exists |

```
Customer phone photo --> OCR / CV --> fault code string
                                              |
                                              v
                    MATCH (p:Product)-[:HAS_ERROR_CODE]->(ec:ErrorCode {code:$code})
                          (ec)-[:INDICATES]->(fm:FailureMode)
                                              |
                                              v
                         ranked FM + CONFIRMS steps + resolution path
```

This notebook is **self-contained**: it does **not** require Neo4j or GPU (Apple MPS / CUDA used if present). It produces images under `notebooks/fault_code_gan_artifacts/`.

---

## Table of contents

| Part | Content |
|------|---------|
| **0** | Setup & domain fault-code catalog |
| **1** | GAN theory (Goodfellow, DCGAN, cGAN) — authoritative sources |
| **2** | Procedural *seed* LCD/LED display images (bootstrap when no real photos) |
| **3** | Dataset, classical augmentations (phone-camera realism) |
| **4** | DCGAN implementation & training |
| **5** | Conditional GAN (class = fault code) |
| **6** | Generate synthetic claim-photo corpus |
| **7** | Lightweight OCR / code extraction eval |
| **8** | Cypher bridge → Neo4j GraphRAG (this codebase) |
| **9** | References & production notes |

---

## Authoritative sources (theory + practice)

| Source | Contribution used here |
|--------|-------------------------|
| Goodfellow et al., *Generative Adversarial Nets*, NeurIPS 2014 | Minimax game \(G\) vs \(D\); value function \(V(D,G)\) |
| Radford, Metz, Chintala, *Unsupervised Representation Learning with Deep Convolutional GANs* (DCGAN), ICLR 2016 | Conv Generator/Discriminator recipes (BatchNorm, LeakyReLU, strided conv, tanh) |
| Mirza & Osindero, *Conditional Generative Adversarial Nets*, 2014 | Class conditioning \(p(x \mid y)\) — generate image **of a chosen fault code** |
| Shorten & Khoshgoftaar, *A survey on Image Data Augmentation for Deep Learning*, J. Big Data 2019 | Geometric/photometric augments as complementary to generative models |
| [PyTorch DCGAN tutorial](https://pytorch.org/tutorials/beginner/dcgan_faces_tutorial.html) | Practical training loop patterns |
| Ho et al. DDPM 2020; Rombach et al. LDM 2022 | *Beyond* GANs for higher fidelity (upgrade path) |
| This repo | `graph/graph_rag.py` (`match_error_codes`, `rank_failure_modes_with_error_codes`), `graph/oem_product_catalog.py` error codes |

> **Honest framing:** When *no* real photos exist, industry practice is **procedural simulation + generative models** (GANs/diffusion) to create a labelled corpus, then **validate OCR on a hold-out of real photos** as soon as any arrive. Do not train production OCR *only* on synthetic data without a real-image gate (see study module 20 in this repo).
