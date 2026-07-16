# Fault-code GAN notebook

**Notebook:** [`fault_code_gan_synthetic_images.ipynb`](./fault_code_gan_synthetic_images.ipynb)
**Adjoining MLOps/CUDA playbook:** [`fault_code_vision_mlops_playbook.ipynb`](./fault_code_vision_mlops_playbook.ipynb)
**Package:** [`../ml/fault_code_vision/`](../ml/fault_code_vision/) — see also [`README-fault-code-vision.md`](./README-fault-code-vision.md)


## Purpose

Generate **synthetic claim-style photos** of appliance LCD/LED fault codes (e.g. `5E`, `UE`, `E24`, `F9E1`) when historical claim images are sparse or missing. Use them to:

1. Train / stress-test OCR or vision extraction
2. Feed extracted codes into GraphRAG Cypher (`ErrorCode` → `INDICATES` → `FailureMode`)
3. Measure end-to-end diagnostic efficacy before real photo volume exists

## Run

```bash
# from repo root (or open the .ipynb in Jupyter / VS Code)
jupyter notebook notebooks/fault_code_gan_synthetic_images.ipynb
```

**Requirements:** `torch`, `torchvision`, `Pillow`, `matplotlib`, `numpy` (already present in a typical local env for this project). Apple MPS or CUDA is used automatically when available.

**Tips:**

- Default training is **12 epochs** each for DCGAN and cGAN (smoke-friendly). Raise to **50–100** for sharper glyphs.
- Artifacts land in `notebooks/fault_code_gan_artifacts/`.
- Optional live Neo4j: start dual graph, load catalog, then call `try_live_neo4j("5E", product_id="wm-001")` in the last code cell.

## Rebuild notebook from sources

Cell sources live under `fault_code_gan_src/` (easier to review/diff than raw `.ipynb` JSON):

```bash
python3 notebooks/fault_code_gan_src/assemble.py
```

## Repo alignment

| Concept | Code path |
|---------|-----------|
| Error code match | `graph/graph_rag.py` → `match_error_codes` |
| Failure-mode boost | `rank_failure_modes_with_error_codes` |
| Catalog codes | `graph/oem_product_catalog.py` |
| Sparse-data philosophy | `docs/24-TBox-Sparse-Data-and-Enterprise-Scale-Patterns.md` |

## Theory sources (in notebook)

Goodfellow et al. 2014 (GAN), Radford et al. 2016 (DCGAN), Mirza & Osindero 2014 (cGAN), Salimans et al. 2016 (label smoothing), Shorten & Khoshgoftaar 2019 (augmentation), PyTorch DCGAN tutorial.
