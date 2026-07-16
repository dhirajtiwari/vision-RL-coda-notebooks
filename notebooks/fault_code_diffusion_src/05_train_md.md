## Part 3 — Train class-conditional DDPM (working code)

We train \(\varepsilon_\theta(x_t, t, y)\) on **full control-panel** seeds (readable digits).

**If samples look like pure noise:** the model is under-trained. Use ≥40–80 epochs (CUDA), or use the on-demand generator with `procedural` / `phone` methods for always-sharp images:

`notebooks/fault_code_image_generator.ipynb`

```bash
python -m ml.fault_code_vision.generate --code 5E --machine washer --methods procedural,phone --n 6
python -m ml.fault_code_diffusion.train --bootstrap --epochs 60 --require-cuda
```
