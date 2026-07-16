## Part 9 — References & further reading

### Foundational papers
1. **I. Goodfellow et al.** — *Generative Adversarial Nets*. NeurIPS 2014.
   https://papers.nips.cc/paper/5423-generative-adversarial-nets
2. **A. Radford, L. Metz, S. Chintala** — *Unsupervised Representation Learning with Deep Convolutional GANs*. ICLR 2016 workshop / arXiv:1511.06434.
3. **M. Mirza, S. Osindero** — *Conditional Generative Adversarial Nets*. arXiv:1411.1784, 2014.
4. **T. Salimans et al.** — *Improved Techniques for Training GANs*. NeurIPS 2016 (label smoothing, feature matching).
5. **I. Gulrajani et al.** — *Improved Training of Wasserstein GANs* (WGAN-GP). NeurIPS 2017 — if mode collapse appears.
6. **C. Shorten, T. Khoshgoftaar** — *A survey on Image Data Augmentation for Deep Learning*. Journal of Big Data, 2019.

### Tutorials & notebooks (implementations)
- PyTorch official DCGAN faces tutorial: https://pytorch.org/tutorials/beginner/dcgan_faces_tutorial.html
- PyTorch examples `dcgan`: https://github.com/pytorch/examples/tree/main/dcgan
- Conditional GAN pattern: class embedding concatenated into G/D (Part 5 of this notebook).
- Higher-fidelity **upgrade path**: DDPM / latent diffusion (Ho et al. 2020; Rombach et al. LDM 2022).

### This repository
- `graph/graph_rag.py` — `match_error_codes`, `rank_failure_modes_with_error_codes`
- `graph/oem_product_catalog.py` — authoritative demo fault codes & INDICATES links
- `docs/24-TBox-Sparse-Data-and-Enterprise-Scale-Patterns.md` — sparse evidence philosophy
- Study module "Synthetic data, MLOps, image generation concepts" (`study/seed_platform_modules.py`)

### Suggested next experiments

| Experiment | Why |
|------------|-----|
| Train longer cGAN (50–100 epochs) or raise `IMG_SIZE` to 128 | Sharper glyphs for OCR |
| WGAN-GP loss | Stability if \(D\) overpowers \(G\) |
| Replace template OCR with EasyOCR / TrOCR fine-tune on `synthetic_corpus` | Production-grade extraction |
| Domain-randomize backgrounds (kitchen, laundry room) via composition | Closer to true claim photos |
| Active learning: prioritize rare codes (`F9E1`) for synthetic oversampling | Class imbalance in claims |

---

### Artifacts written by this notebook

```text
notebooks/fault_code_gan_artifacts/
  seed_lcd/                  # procedural LCD seeds
  augmented/                 # seeds + classical augments (GAN train set)
  generated/                 # DCGAN/cGAN grids + corpus/
  checkpoints/dcgan.pt
  checkpoints/cgan.pt
  seed_manifest.json
  train_manifest.json
  synthetic_corpus_manifest.json
  ocr_eval_report.json
  preview_*.png
```

**Done when:** you can generate labelled claim-style images for every catalog code, run the extraction harness, and emit Cypher that matches this product's GraphRAG contracts.
