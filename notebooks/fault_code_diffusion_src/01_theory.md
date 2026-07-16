## Part 1 — Theory (latest mainstream methods)

### 1.1 DDPM — Denoising Diffusion Probabilistic Models (Ho et al., NeurIPS 2020)

**Forward (destroy):** add Gaussian noise over \(T\) steps

\[
q(x_t \mid x_{t-1}) = \mathcal{N}\big(x_t; \sqrt{1-\beta_t}\, x_{t-1},\, \beta_t I\big)
\]

Closed form:

\[
x_t = \sqrt{\bar\alpha_t}\, x_0 + \sqrt{1-\bar\alpha_t}\,\varepsilon, \quad \varepsilon\sim\mathcal{N}(0,I)
\]

where \(\alpha_t = 1-\beta_t\), \(\bar\alpha_t = \prod_{s=1}^t \alpha_s\).

**Reverse (generate):** learn noise predictor \(\varepsilon_\theta(x_t, t, y)\) (optional class \(y\)):

\[
L = \mathbb{E}_{x_0,\varepsilon,t,y}\big\| \varepsilon - \varepsilon_\theta(x_t, t, y) \big\|_2^2
\]

### 1.2 Faster sampling

| Method | Idea |
|--------|------|
| **DDIM** (Song et al. 2021) | Non-Markovian reverse → 20–50 steps |
| **DPM-Solver / DPM-Solver++** | ODE solvers for diffusion → few steps |
| **Latent Diffusion (LDM)** (Rombach et al. CVPR 2022) | Diffuse in VAE latent space (Stable Diffusion family) |
| **Classifier-free guidance** (Ho & Salimans) | Mix conditional/unconditional scores for stronger control |

### 1.3 Product mapping

```text
y = fault code class (5E, UE, …)
x0 = LCD / claim-crop image
Train ε_θ on seeds + augments (+ real photos when available)
Sample many x0|y  →  OCR train / eval corpus  →  GraphRAG still uses extracted code
```

### 1.4 GAN vs diffusion (this monorepo)

See `ml.fault_code_diffusion.pipeline.diffusion_vs_gan()` in the next cells.
