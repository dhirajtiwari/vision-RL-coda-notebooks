"""Small class-conditional U-Net for 64×64 DDPM (showcase scale)."""

from __future__ import annotations

import math

import torch
import torch.nn as nn


class SinusoidalPosEmb(nn.Module):
    def __init__(self, dim: int):
        super().__init__()
        self.dim = dim

    def forward(self, t: torch.Tensor) -> torch.Tensor:
        half = self.dim // 2
        freqs = torch.exp(-math.log(10000) * torch.arange(half, device=t.device) / (half - 1))
        args = t.float().unsqueeze(1) * freqs.unsqueeze(0)
        return torch.cat([args.sin(), args.cos()], dim=-1)


class ResBlock(nn.Module):
    def __init__(self, in_ch: int, out_ch: int, emb_dim: int):
        super().__init__()
        self.norm1 = nn.GroupNorm(8, in_ch)
        self.conv1 = nn.Conv2d(in_ch, out_ch, 3, padding=1)
        self.emb_proj = nn.Linear(emb_dim, out_ch)
        self.norm2 = nn.GroupNorm(8, out_ch)
        self.conv2 = nn.Conv2d(out_ch, out_ch, 3, padding=1)
        self.skip = nn.Conv2d(in_ch, out_ch, 1) if in_ch != out_ch else nn.Identity()
        self.act = nn.SiLU()

    def forward(self, x: torch.Tensor, emb: torch.Tensor) -> torch.Tensor:
        h = self.conv1(self.act(self.norm1(x)))
        h = h + self.emb_proj(self.act(emb))[:, :, None, None]
        h = self.conv2(self.act(self.norm2(h)))
        return h + self.skip(x)


class CondUNet(nn.Module):
    """ε-prediction U-Net conditioned on diffusion step t and class label."""

    def __init__(
        self,
        n_classes: int,
        in_ch: int = 3,
        base: int = 64,
        emb_dim: int = 256,
    ):
        super().__init__()
        self.time_mlp = nn.Sequential(
            SinusoidalPosEmb(base),
            nn.Linear(base, emb_dim),
            nn.SiLU(),
            nn.Linear(emb_dim, emb_dim),
        )
        self.label_emb = nn.Embedding(n_classes, emb_dim)

        self.in_conv = nn.Conv2d(in_ch, base, 3, padding=1)
        self.down1 = ResBlock(base, base, emb_dim)
        self.down2 = ResBlock(base, base * 2, emb_dim)
        self.pool = nn.AvgPool2d(2)
        self.mid = ResBlock(base * 2, base * 2, emb_dim)
        self.up1 = ResBlock(base * 4, base, emb_dim)  # skip concat
        self.up2 = ResBlock(base * 2, base, emb_dim)
        self.out = nn.Sequential(
            nn.GroupNorm(8, base),
            nn.SiLU(),
            nn.Conv2d(base, in_ch, 3, padding=1),
        )
        self.upsample = nn.Upsample(scale_factor=2, mode="nearest")

    def forward(self, x: torch.Tensor, t: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
        emb = self.time_mlp(t) + self.label_emb(y)
        h0 = self.in_conv(x)
        h1 = self.down1(h0, emb)
        h2 = self.down2(self.pool(h1), emb)
        h = self.mid(self.pool(h2), emb)
        h = self.upsample(h)
        h = self.up1(torch.cat([h, h2], dim=1), emb)
        h = self.upsample(h)
        h = self.up2(torch.cat([h, h1], dim=1), emb)
        return self.out(h)
