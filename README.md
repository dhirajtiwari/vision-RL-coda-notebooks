# Vision + RL + CUDA notebooks

Client showcase for warranty fault-code **image generation**, **OCR**, **diffusion**, and **diagnostic RL**.

## Start here

1. Read [`notebooks/00-FAULT-CODE-ML-INDEX.md`](notebooks/00-FAULT-CODE-ML-INDEX.md)
2. Open **`notebooks/fault_code_image_generator.ipynb`** — enter fault code + machine → images

```bash
git clone https://github.com/dhirajtiwari/vision-RL-coda-notebooks.git
cd vision-RL-coda-notebooks
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-ml.txt

# sharp diverse images (no long train)
python -m ml.fault_code_vision.generate --code 5E --machine washer --methods procedural,phone --n 6

jupyter notebook notebooks/
```

Training data is **procedurally simulated** (rooms, finishes, LCD styles) — not real claim photos — so models learn that simulated distribution. See `describe_data_provenance()` in the generator notebook.
