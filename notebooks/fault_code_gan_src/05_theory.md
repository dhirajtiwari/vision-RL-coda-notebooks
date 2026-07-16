## Part 1 — GAN principles (authoritative theory)

### 1.1 The adversarial game (Goodfellow et al., 2014)

Two networks train jointly:

- **Generator** \(G(z)\): maps noise \(z \sim p_z\) (usually \(\mathcal{N}(0,I)\)) to a fake sample \(\tilde{x}\).
- **Discriminator** \(D(x)\): outputs probability that \(x\) is real.

Value function:

\[
\min_G \max_D V(D,G)
= \mathbb{E}_{x \sim p_{\mathrm{data}}}[\log D(x)]
+ \mathbb{E}_{z \sim p_z}[\log(1 - D(G(z)))]
\]

**Intuition:** \(D\) learns to tell real LCD photos from fakes; \(G\) learns to fool \(D\). At equilibrium, \(G\) samples from the data distribution.

**Training practice (non-saturating heuristic):** train \(G\) to **maximize** \(\log D(G(z))\) instead of minimize \(\log(1-D(G(z)))\) — gradients stay informative early in training (Goodfellow 2014, §3).

### 1.2 DCGAN architectural constraints (Radford et al., 2016)

| Rule | Implementation |
|------|----------------|
| No pooling — use strided conv / fractionally-strided conv | `Conv2d` / `ConvTranspose2d` |
| BatchNorm in \(G\) and \(D\) (except \(G\) output & \(D\) input) | `BatchNorm2d` |
| ReLU in \(G\) (except `Tanh` output); LeakyReLU in \(D\) | `nn.ReLU`, `nn.LeakyReLU(0.2)` |
| Normalize inputs to \([-1,1]\) for `Tanh` | `transforms.Normalize(0.5, 0.5)` |

### 1.3 Conditional GAN (Mirza & Osindero, 2014)

We need images of a **specific** fault code (`5E` vs `UE`). Condition both networks on label \(y\):

\[
\min_G \max_D V(D,G)
= \mathbb{E}[\log D(x \mid y)] + \mathbb{E}[\log(1 - D(G(z \mid y)))]
\]

Class embedding is concatenated (or projected) into \(G\) and \(D\).

### 1.4 Why GANs for *this* sparse-data problem

| Approach | Role |
|----------|------|
| **Classical augments** (rotate, blur, glare) | Cheap diversity from few seeds — always do this |
| **Procedural LCD renderer** | Bootstrap labelled ground-truth codes without real photos |
| **DCGAN / cGAN** | Learn residual distribution of textures, fonts, glare, sensor noise beyond hand-coded rules |
| **Diffusion (upgrade)** | Higher fidelity / stability for production OCR corpora |

Sparse-data pattern in this product's docs (`docs/24-…`): when ABox/evidence is thin, **synthetic completion + validation gates** beat pretending the graph is complete.
