"""DDPM noise schedule (Ho et al., 2020).

Forward process:
  q(x_t | x_0) = N(x_t; √ᾱ_t x_0, (1-ᾱ_t) I)

  x_t = √ᾱ_t x_0 + √(1-ᾱ_t) ε,   ε ~ N(0,I)
"""

from __future__ import annotations

import torch


def linear_beta_schedule(T: int, beta_start: float = 1e-4, beta_end: float = 0.02) -> torch.Tensor:
    return torch.linspace(beta_start, beta_end, T)


def cosine_beta_schedule(T: int, s: float = 0.008) -> torch.Tensor:
    """Nichol & Dhariwal improved DDPM cosine schedule."""
    steps = T + 1
    x = torch.linspace(0, T, steps)
    alphas_cumprod = torch.cos(((x / T) + s) / (1 + s) * torch.pi * 0.5) ** 2
    alphas_cumprod = alphas_cumprod / alphas_cumprod[0]
    betas = 1 - (alphas_cumprod[1:] / alphas_cumprod[:-1])
    return torch.clip(betas, 0.0001, 0.9999)


class DiffusionSchedule:
    def __init__(self, T: int = 200, schedule: str = "cosine", device: torch.device | None = None):
        self.T = T
        betas = cosine_beta_schedule(T) if schedule == "cosine" else linear_beta_schedule(T)
        if device is not None:
            betas = betas.to(device)
        alphas = 1.0 - betas
        alphas_cumprod = torch.cumprod(alphas, dim=0)
        alphas_cumprod_prev = torch.cat([torch.ones(1, device=betas.device), alphas_cumprod[:-1]])

        self.betas = betas
        self.alphas = alphas
        self.alphas_cumprod = alphas_cumprod
        self.alphas_cumprod_prev = alphas_cumprod_prev
        self.sqrt_alphas_cumprod = torch.sqrt(alphas_cumprod)
        self.sqrt_one_minus_alphas_cumprod = torch.sqrt(1.0 - alphas_cumprod)
        self.sqrt_recip_alphas = torch.sqrt(1.0 / alphas)
        # posterior variance β̃_t
        self.posterior_variance = betas * (1.0 - alphas_cumprod_prev) / (1.0 - alphas_cumprod)

    def _extract(self, a: torch.Tensor, t: torch.Tensor, x_shape: torch.Size) -> torch.Tensor:
        out = a.gather(0, t)
        return out.reshape(t.shape[0], *((1,) * (len(x_shape) - 1)))

    def q_sample(self, x0: torch.Tensor, t: torch.Tensor, noise: torch.Tensor | None = None) -> torch.Tensor:
        """Diffuse x0 to timestep t."""
        if noise is None:
            noise = torch.randn_like(x0)
        return (
            self._extract(self.sqrt_alphas_cumprod, t, x0.shape) * x0
            + self._extract(self.sqrt_one_minus_alphas_cumprod, t, x0.shape) * noise
        )

    def p_mean_variance(
        self,
        model_out: torch.Tensor,
        x_t: torch.Tensor,
        t: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Predict x0 from noise, then posterior mean of q(x_{t-1}|x_t,x0)."""
        # model predicts ε; x0 = (x_t − √(1−ᾱ) ε) / √ᾱ
        sqrt_ac = self._extract(self.sqrt_alphas_cumprod, t, x_t.shape)
        sqrt_om_ac = self._extract(self.sqrt_one_minus_alphas_cumprod, t, x_t.shape)
        pred_x0 = (x_t - sqrt_om_ac * model_out) / sqrt_ac.clamp(min=1e-5)
        pred_x0 = pred_x0.clamp(-1.0, 1.0)

        ac_prev = self._extract(self.alphas_cumprod_prev, t, x_t.shape)
        ac = self._extract(self.alphas_cumprod, t, x_t.shape)
        beta = self._extract(self.betas, t, x_t.shape)
        # posterior mean coefficients
        coef1 = torch.sqrt(ac_prev) * beta / (1.0 - ac).clamp(min=1e-5)
        coef2 = torch.sqrt(self._extract(self.alphas, t, x_t.shape)) * (1.0 - ac_prev) / (1.0 - ac).clamp(min=1e-5)
        mean = coef1 * pred_x0 + coef2 * x_t
        var = self._extract(self.posterior_variance, t, x_t.shape)
        return mean, var
