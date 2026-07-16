"""CLI: train conditional DDPM on fault-code image manifest.

  python -m ml.fault_code_diffusion.train \\
    --manifest notebooks/fault_code_gan_artifacts/ocr_demo/ocr_train_manifest.json \\
    --epochs 40 --out notebooks/fault_code_diffusion_artifacts
"""

from __future__ import annotations

import argparse
from pathlib import Path

from ml.fault_code_diffusion.ddpm import DDPMConfig, train_ddpm
from ml.fault_code_vision.pipeline import bootstrap_demo_dataset


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Train class-conditional DDPM for fault codes")
    p.add_argument("--manifest", type=Path, default=None)
    p.add_argument("--bootstrap", action="store_true", help="Create seed dataset if no manifest")
    p.add_argument("--epochs", type=int, default=25)
    p.add_argument("--batch-size", type=int, default=32)
    p.add_argument("--T", type=int, default=200, help="Diffusion timesteps")
    p.add_argument("--out", type=Path, default=Path("notebooks/fault_code_diffusion_artifacts"))
    p.add_argument("--require-cuda", action="store_true")
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args(argv)

    manifest = args.manifest
    if manifest is None or args.bootstrap:
        art = args.out / "dataset"
        manifest = bootstrap_demo_dataset(art, n_per_code=24, image_size=64)
        print("bootstrap manifest:", manifest)

    train_ddpm(
        manifest,
        args.out,
        DDPMConfig(
            T=args.T,
            epochs=args.epochs,
            batch_size=args.batch_size,
            seed=args.seed,
            require_cuda=args.require_cuda,
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
