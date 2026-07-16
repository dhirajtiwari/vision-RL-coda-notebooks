"""Conditional GAN for fault-code panels (package form of notebook cGAN)."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision.utils import save_image

from ml.fault_code_vision.catalog import CODE_TO_IDX, IDX_TO_CODE, N_CLASSES
from ml.fault_code_vision.dataset import FaultCodeImageDataset, load_manifest, save_manifest
from ml.fault_code_vision.device import assert_cuda_for_client_train, pick_device

MACHINE_OK = {"washer", "dryer", "dishwasher", "fridge", "generic"}


class CondGenerator(nn.Module):
    def __init__(
        self,
        n_classes: int = N_CLASSES,
        nz: int = 100,
        ngf: int = 64,
        nc: int = 3,
        emb_dim: int = 50,
    ):
        super().__init__()
        self.nz = nz
        self.label_emb = nn.Embedding(n_classes, emb_dim)
        self.net = nn.Sequential(
            nn.ConvTranspose2d(nz + emb_dim, ngf * 8, 4, 1, 0, bias=False),
            nn.BatchNorm2d(ngf * 8),
            nn.ReLU(True),
            nn.ConvTranspose2d(ngf * 8, ngf * 4, 4, 2, 1, bias=False),
            nn.BatchNorm2d(ngf * 4),
            nn.ReLU(True),
            nn.ConvTranspose2d(ngf * 4, ngf * 2, 4, 2, 1, bias=False),
            nn.BatchNorm2d(ngf * 2),
            nn.ReLU(True),
            nn.ConvTranspose2d(ngf * 2, ngf, 4, 2, 1, bias=False),
            nn.BatchNorm2d(ngf),
            nn.ReLU(True),
            nn.ConvTranspose2d(ngf, nc, 4, 2, 1, bias=False),
            nn.Tanh(),
        )

    def forward(self, z: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
        emb = self.label_emb(labels).unsqueeze(2).unsqueeze(3)
        return self.net(torch.cat([z, emb], dim=1))


class CondDiscriminator(nn.Module):
    def __init__(
        self,
        n_classes: int = N_CLASSES,
        ndf: int = 64,
        nc: int = 3,
        emb_dim: int = 50,
    ):
        super().__init__()
        self.emb_dim = emb_dim
        self.label_emb = nn.Embedding(n_classes, emb_dim)
        self.net = nn.Sequential(
            nn.Conv2d(nc + emb_dim, ndf, 4, 2, 1, bias=False),
            nn.LeakyReLU(0.2, inplace=True),
            nn.Conv2d(ndf, ndf * 2, 4, 2, 1, bias=False),
            nn.BatchNorm2d(ndf * 2),
            nn.LeakyReLU(0.2, inplace=True),
            nn.Conv2d(ndf * 2, ndf * 4, 4, 2, 1, bias=False),
            nn.BatchNorm2d(ndf * 4),
            nn.LeakyReLU(0.2, inplace=True),
            nn.Conv2d(ndf * 4, ndf * 8, 4, 2, 1, bias=False),
            nn.BatchNorm2d(ndf * 8),
            nn.LeakyReLU(0.2, inplace=True),
            nn.Conv2d(ndf * 8, 1, 4, 1, 0, bias=False),
        )

    def forward(self, x: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
        b, _, h, w = x.shape
        emb = self.label_emb(labels).unsqueeze(2).unsqueeze(3).expand(b, self.emb_dim, h, w)
        return self.net(torch.cat([x, emb], dim=1)).view(-1)


def _weights_init(m: nn.Module) -> None:
    name = m.__class__.__name__
    if "Conv" in name:
        nn.init.normal_(m.weight.data, 0.0, 0.02)
    elif "BatchNorm" in name:
        nn.init.normal_(m.weight.data, 1.0, 0.02)
        nn.init.constant_(m.bias.data, 0)


@dataclass
class CGANConfig:
    epochs: int = 25
    batch_size: int = 64
    lr: float = 2e-4
    nz: int = 100
    image_size: int = 64
    require_cuda: bool = False
    seed: int = 42


def build_panel_manifest(
    out_dir: Path,
    n_per_code: int = 40,
    size: int = 64,
    machines: list[str] | None = None,
    phone_aug_frac: float = 0.35,
) -> Path:
    """Create *diverse* domain-randomized seeds for cGAN / diffusion training.

    Uses render_training_variant (room scenes, finishes, LCD styles, framing).
    Without this diversity, models only learn dark-on-black panels.
    """
    from ml.fault_code_vision.catalog import FAULT_CATALOG
    from ml.fault_code_vision.panel_render import render_training_variant

    machines = machines or ["washer", "dryer", "dishwasher", "fridge"]
    out_dir = Path(out_dir)
    img_dir = out_dir / "panels"
    img_dir.mkdir(parents=True, exist_ok=True)
    for p in img_dir.glob("*.png"):
        p.unlink()
    rows = []
    for row in FAULT_CATALOG:
        code = row["code"]
        fam = row.get("family", "generic")
        machine = fam if fam in MACHINE_OK else "generic"
        for i in range(n_per_code):
            m = machines[i % len(machines)] if fam == "generic" else machine
            use_phone = (i % 5 == 0) or (i / max(n_per_code, 1) < phone_aug_frac and i % 2 == 0)
            img = render_training_variant(
                code,
                machine=m,
                size=size,
                seed=i + 17 * CODE_TO_IDX[code],
                phone_aug=use_phone,
            )
            path = img_dir / f"{code}__{m}__{i:03d}.png"
            img.save(path)
            rows.append(
                {
                    "path": str(path.resolve()),
                    "code": code,
                    "class_idx": CODE_TO_IDX[code],
                    "machine": m,
                    "split": "train",
                    "source": "panel_seed_diverse" if not use_phone else "panel_seed_phone",
                }
            )
    man = out_dir / "panel_manifest.json"
    save_manifest(rows, man)
    print(f"Built diverse train set: {len(rows)} images → {img_dir}")
    return man


def train_cgan(manifest: Path, out_dir: Path, cfg: CGANConfig | None = None) -> Path:
    cfg = cfg or CGANConfig()
    torch.manual_seed(cfg.seed)
    device = assert_cuda_for_client_train(allow_cpu_fallback=not cfg.require_cuda)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = load_manifest(manifest)
    ds = FaultCodeImageDataset(rows, image_size=cfg.image_size, for_classifier=False)
    loader = DataLoader(ds, batch_size=cfg.batch_size, shuffle=True, drop_last=True, num_workers=0)

    G = CondGenerator(nz=cfg.nz).to(device)
    D = CondDiscriminator().to(device)
    G.apply(_weights_init)
    D.apply(_weights_init)
    opt_g = torch.optim.Adam(G.parameters(), lr=cfg.lr, betas=(0.5, 0.999))
    opt_d = torch.optim.Adam(D.parameters(), lr=cfg.lr, betas=(0.5, 0.999))
    bce = nn.BCEWithLogitsLoss()

    t0 = time.time()
    for epoch in range(1, cfg.epochs + 1):
        for real, labels, _ in loader:
            real, labels = real.to(device), labels.to(device)
            bsz = real.size(0)
            # D
            opt_d.zero_grad(set_to_none=True)
            loss_d = bce(D(real, labels), torch.full((bsz,), 0.9, device=device))
            z = torch.randn(bsz, cfg.nz, 1, 1, device=device)
            fake = G(z, labels)
            loss_d = loss_d + bce(D(fake.detach(), labels), torch.zeros(bsz, device=device))
            loss_d.backward()
            opt_d.step()
            # G
            opt_g.zero_grad(set_to_none=True)
            z = torch.randn(bsz, cfg.nz, 1, 1, device=device)
            gen_y = torch.randint(0, N_CLASSES, (bsz,), device=device)
            fake = G(z, gen_y)
            loss_g = bce(D(fake, gen_y), torch.full((bsz,), 0.9, device=device))
            loss_g.backward()
            opt_g.step()
        print(f"[cGAN {epoch:03d}/{cfg.epochs}] loss_D={loss_d.item():.3f} loss_G={loss_g.item():.3f}")

    path = out_dir / "cgan.pt"
    torch.save(
        {
            "G": G.state_dict(),
            "nz": cfg.nz,
            "n_classes": N_CLASSES,
            "idx_to_code": IDX_TO_CODE,
            "image_size": cfg.image_size,
        },
        path,
    )
    print(f"cGAN saved {path} in {time.time() - t0:.1f}s")
    return path


@torch.no_grad()
def sample_cgan(
    ckpt: Path,
    code: str,
    n: int = 4,
    out_dir: Path | None = None,
) -> list[Path]:
    device = pick_device()
    data = torch.load(ckpt, map_location=device, weights_only=False)
    G = CondGenerator(n_classes=int(data["n_classes"]), nz=int(data["nz"])).to(device)
    G.load_state_dict(data["G"])
    G.eval()
    code = code.upper()
    if code not in CODE_TO_IDX:
        raise KeyError(f"Unknown code {code}; known={list(CODE_TO_IDX)}")
    y = torch.full((n,), CODE_TO_IDX[code], device=device, dtype=torch.long)
    z = torch.randn(n, int(data["nz"]), 1, 1, device=device)
    fake = G(z, y).cpu()
    fake = (fake * 0.5 + 0.5).clamp(0, 1)
    out_dir = Path(out_dir or Path(ckpt).parent / "samples")
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for i in range(n):
        p = out_dir / f"gan__{code}__{i:03d}.png"
        save_image(fake[i], p)
        paths.append(p)
    return paths
