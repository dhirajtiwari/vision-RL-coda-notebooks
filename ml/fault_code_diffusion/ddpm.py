"""Train & sample class-conditional DDPM for fault-code displays."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path

import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader
from torchvision.utils import make_grid, save_image

from ml.fault_code_diffusion.device import assert_cuda_for_client_train, device_report
from ml.fault_code_diffusion.schedule import DiffusionSchedule
from ml.fault_code_diffusion.unet import CondUNet
from ml.fault_code_vision.catalog import IDX_TO_CODE, N_CLASSES
from ml.fault_code_vision.dataset import FaultCodeImageDataset, load_manifest


@dataclass
class DDPMConfig:
    T: int = 200
    schedule: str = "cosine"
    epochs: int = 30
    batch_size: int = 32
    lr: float = 2e-4
    image_size: int = 64
    base_channels: int = 64
    seed: int = 42
    require_cuda: bool = False


@torch.no_grad()
def p_sample_loop(
    model: CondUNet,
    schedule: DiffusionSchedule,
    labels: torch.Tensor,
    shape: tuple[int, ...],
    device: torch.device,
) -> torch.Tensor:
    """Ancestral DDPM sampling from pure noise, class-conditional."""
    model.eval()
    x = torch.randn(shape, device=device)
    B = shape[0]
    for i in reversed(range(schedule.T)):
        t = torch.full((B,), i, device=device, dtype=torch.long)
        eps = model(x, t, labels)
        mean, var = schedule.p_mean_variance(eps, x, t)
        if i > 0:
            noise = torch.randn_like(x)
            x = mean + torch.sqrt(var.clamp(min=1e-20)) * noise
        else:
            x = mean
    return x.clamp(-1, 1)


def train_ddpm(
    manifest: str | Path,
    out_dir: str | Path,
    cfg: DDPMConfig | None = None,
) -> dict:
    cfg = cfg or DDPMConfig()
    torch.manual_seed(cfg.seed)
    device = assert_cuda_for_client_train(allow_cpu_fallback=not cfg.require_cuda)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "samples").mkdir(exist_ok=True)

    rows = load_manifest(manifest)
    # use all rows for small showcase trains
    ds = FaultCodeImageDataset(rows, image_size=cfg.image_size, for_classifier=False)
    loader = DataLoader(ds, batch_size=cfg.batch_size, shuffle=True, num_workers=0, drop_last=True)

    schedule = DiffusionSchedule(T=cfg.T, schedule=cfg.schedule, device=device)
    model = CondUNet(n_classes=N_CLASSES, base=cfg.base_channels).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=cfg.lr)

    history = []
    t0 = time.time()
    model.train()
    for epoch in range(1, cfg.epochs + 1):
        losses = []
        for x, y, _codes in loader:
            x = x.to(device)
            y = y.to(device)
            B = x.size(0)
            t = torch.randint(0, schedule.T, (B,), device=device)
            noise = torch.randn_like(x)
            x_t = schedule.q_sample(x, t, noise)
            pred = model(x_t, t, y)
            loss = F.mse_loss(pred, noise)
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()
            losses.append(loss.item())
        mean_loss = sum(losses) / max(len(losses), 1)
        history.append({"epoch": epoch, "loss": mean_loss})
        print(f"[DDPM {epoch:03d}/{cfg.epochs}] loss={mean_loss:.4f}")

        if epoch == 1 or epoch % max(1, cfg.epochs // 5) == 0 or epoch == cfg.epochs:
            # sample a grid: one row-ish of classes
            n = min(16, N_CLASSES)
            labels = torch.arange(n, device=device)
            samples = p_sample_loop(model, schedule, labels, (n, 3, cfg.image_size, cfg.image_size), device)
            grid = make_grid(samples, nrow=4, normalize=True, value_range=(-1, 1))
            save_image(grid, out_dir / "samples" / f"epoch_{epoch:03d}.png")
            codes = [IDX_TO_CODE[i] for i in range(n)]
            print("  sample codes:", codes)

    ckpt = {
        "model": model.state_dict(),
        "T": cfg.T,
        "schedule": cfg.schedule,
        "n_classes": N_CLASSES,
        "image_size": cfg.image_size,
        "base_channels": cfg.base_channels,
        "idx_to_code": IDX_TO_CODE,
        "history": history,
        "device_report": device_report(),
    }
    path = out_dir / "ddpm.pt"
    torch.save(ckpt, path)
    (out_dir / "metrics.json").write_text(
        json.dumps(
            {
                "final_loss": history[-1]["loss"] if history else None,
                "epochs": cfg.epochs,
                "seconds": time.time() - t0,
                "device": str(device),
            },
            indent=2,
        )
    )
    print(f"saved {path} in {time.time() - t0:.1f}s")
    return {"model": model, "schedule": schedule, "device": device, "ckpt_path": path, "history": history}


@torch.no_grad()
def generate_codes(
    ckpt_path: str | Path,
    codes: list[str],
    out_dir: str | Path,
    n_per_code: int = 4,
) -> list[Path]:
    """Generate images for named fault codes from a trained checkpoint."""
    from ml.fault_code_vision.catalog import CODE_TO_IDX

    device = assert_cuda_for_client_train(allow_cpu_fallback=True)
    ckpt = torch.load(ckpt_path, map_location=device, weights_only=False)
    model = CondUNet(
        n_classes=int(ckpt["n_classes"]),
        base=int(ckpt.get("base_channels", 64)),
    ).to(device)
    model.load_state_dict(ckpt["model"])
    model.eval()
    schedule = DiffusionSchedule(T=int(ckpt["T"]), schedule=ckpt.get("schedule", "cosine"), device=device)
    size = int(ckpt["image_size"])
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for code in codes:
        code_u = code.upper()
        if code_u not in CODE_TO_IDX:
            raise KeyError(f"Unknown code {code}")
        labels = torch.full((n_per_code,), CODE_TO_IDX[code_u], device=device, dtype=torch.long)
        samples = p_sample_loop(model, schedule, labels, (n_per_code, 3, size, size), device)
        for j in range(n_per_code):
            p = out_dir / f"diff__{code_u}__{j:03d}.png"
            save_image(samples[j], p, normalize=True, value_range=(-1, 1))
            paths.append(p)
    return paths
