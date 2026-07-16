"""Unified fault-code image generation API.

Input: fault code + machine type (+ method)
Output: a set of PNGs (procedural crisp panels, phone-claim style, cGAN, diffusion)

CLI:
  python -m ml.fault_code_vision.generate --code 5E --machine washer --n 6 \\
      --methods procedural,phone,gan,diffusion
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from PIL import Image

from ml.fault_code_vision.catalog import CODE_TO_IDX, FAULT_CATALOG, is_closed_set_code
from ml.fault_code_vision.panel_render import (
    MACHINE_THEMES,
    describe_data_provenance,
    render_full_panel,
    render_training_variant,
)

DEFAULT_METHODS = ("procedural", "phone")


def _resolve_machine(machine: str | None, code: str) -> str:
    if machine:
        m = machine.lower().strip()
        if m in MACHINE_THEMES:
            return m
        raise ValueError(f"Unknown machine={machine!r}; choose from {list(MACHINE_THEMES)}")
    # default from catalog family
    for row in FAULT_CATALOG:
        if row["code"] == code.upper():
            fam = row.get("family", "generic")
            return fam if fam in MACHINE_THEMES else "generic"
    return "generic"


def generate_procedural(
    code: str,
    machine: str,
    n: int,
    out_dir: Path,
    size: int = 256,
) -> list[Path]:
    """Diverse clean panels: different rooms, finishes, LCD styles, framing."""
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for i in range(n):
        # cycle framing / look via seed so a batch is visually varied
        img = render_full_panel(
            code,
            machine=machine,
            size=size,
            seed=i * 13 + 3,
            include_scene=True,
            framing=["tight", "panel", "wide", "panel", "wide", "tight"][i % 6],
        )
        p = out_dir / f"proc__{machine}__{code}__{i:03d}.png"
        img.save(p)
        paths.append(p)
    return paths


def generate_phone(
    code: str,
    machine: str,
    n: int,
    out_dir: Path,
    size: int = 256,
) -> list[Path]:
    """Claim-photo style: diverse scenes + phone degradations (not black letterbox)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for i in range(n):
        img = render_training_variant(
            code,
            machine=machine,
            size=size,
            seed=2000 + i * 17,
            phone_aug=True,
        )
        p = out_dir / f"phone__{machine}__{code}__{i:03d}.png"
        img.save(p)
        paths.append(p)
    return paths


def generate_gan(
    code: str,
    n: int,
    out_dir: Path,
    ckpt: Path | None = None,
    auto_train: bool = True,
    train_epochs: int = 20,
    artifacts: Path | None = None,
) -> list[Path]:
    from ml.fault_code_vision.cgan import build_panel_manifest, sample_cgan, train_cgan

    artifacts = Path(artifacts or "notebooks/fault_code_gen_artifacts")
    ckpt = Path(ckpt or artifacts / "cgan" / "cgan.pt")
    if not ckpt.exists():
        if not auto_train:
            raise FileNotFoundError(f"cGAN checkpoint missing: {ckpt}")
        print(
            f"cGAN ckpt not found — training {train_epochs} epochs on *diverse* panels "
            "(rooms/finishes/LCD styles; not black-only)…"
        )
        man = build_panel_manifest(artifacts / "cgan_data", n_per_code=36, size=64)
        from ml.fault_code_vision.cgan import CGANConfig

        ckpt = train_cgan(man, artifacts / "cgan", CGANConfig(epochs=train_epochs))
    return sample_cgan(ckpt, code, n=n, out_dir=out_dir)


def generate_diffusion(
    code: str,
    n: int,
    out_dir: Path,
    ckpt: Path | None = None,
    auto_train: bool = True,
    train_epochs: int = 40,
    artifacts: Path | None = None,
) -> list[Path]:
    from ml.fault_code_diffusion.ddpm import DDPMConfig, generate_codes, train_ddpm
    from ml.fault_code_vision.cgan import build_panel_manifest

    artifacts = Path(artifacts or "notebooks/fault_code_gen_artifacts")
    ckpt = Path(ckpt or artifacts / "diffusion" / "ddpm.pt")
    if not ckpt.exists():
        if not auto_train:
            raise FileNotFoundError(f"DDPM checkpoint missing: {ckpt}")
        print(
            f"Diffusion ckpt not found — training {train_epochs} epochs on *diverse* panels "
            "(rooms/finishes; longer train = less noise)…"
        )
        man = build_panel_manifest(artifacts / "diff_data", n_per_code=40, size=64)
        train_ddpm(
            man,
            artifacts / "diffusion",
            DDPMConfig(T=200, epochs=train_epochs, batch_size=32, require_cuda=False),
        )
        ckpt = artifacts / "diffusion" / "ddpm.pt"
    return generate_codes(ckpt, [code], out_dir=out_dir, n_per_code=n)


def generate_images(
    fault_code: str,
    machine: str | None = None,
    n: int = 4,
    methods: Iterable[str] = DEFAULT_METHODS,
    out_dir: str | Path | None = None,
    size: int = 256,
    auto_train: bool = True,
    gan_epochs: int = 20,
    diffusion_epochs: int = 40,
    gan_ckpt: str | Path | None = None,
    diffusion_ckpt: str | Path | None = None,
) -> dict[str, Any]:
    """
    Generate a fresh set of images for one fault code + machine.

    methods:
      - procedural : sharp full control panel (always readable)
      - phone      : procedural + phone-camera realism
      - gan        : conditional GAN samples (trains if needed)
      - diffusion  : conditional DDPM samples (trains if needed; needs enough epochs)
    """
    code = fault_code.upper().strip()
    if not is_closed_set_code(code):
        known = ", ".join(sorted(CODE_TO_IDX))
        raise ValueError(f"Unknown fault code {code!r}. Closed set: {known}")

    machine_r = _resolve_machine(machine, code)
    methods_l = [m.strip().lower() for m in methods]

    # Resolve output dir relative to repo root even if cwd is notebooks/
    if out_dir is None:
        cwd = Path(".").resolve()
        if (cwd / "ml").is_dir():
            out_dir = cwd / "notebooks" / "fault_code_gen_artifacts" / "requests"
        elif (cwd.parent / "ml").is_dir():
            out_dir = cwd.parent / "notebooks" / "fault_code_gen_artifacts" / "requests"
        else:
            out_dir = cwd / "fault_code_gen_artifacts" / "requests"
    root = Path(out_dir) / f"{machine_r}_{code}"
    root.mkdir(parents=True, exist_ok=True)

    results: dict[str, list[str]] = {}
    for method in methods_l:
        mdir = root / method
        if method == "procedural":
            paths = generate_procedural(code, machine_r, n, mdir, size=size)
        elif method in {"phone", "claim", "augment"}:
            paths = generate_phone(code, machine_r, n, mdir, size=size)
        elif method == "gan":
            paths = generate_gan(
                code,
                n,
                mdir,
                ckpt=Path(gan_ckpt) if gan_ckpt else None,
                auto_train=auto_train,
                train_epochs=gan_epochs,
            )
        elif method in {"diffusion", "ddpm"}:
            paths = generate_diffusion(
                code,
                n,
                mdir,
                ckpt=Path(diffusion_ckpt) if diffusion_ckpt else None,
                auto_train=auto_train,
                train_epochs=diffusion_epochs,
            )
        else:
            raise ValueError(f"Unknown method {method!r}; use procedural|phone|gan|diffusion")
        results[method] = [str(p) for p in paths]

    # contact sheet of procedural (always sharp)
    try:
        _write_contact_sheet(results, root / "contact_sheet.png", size=size)
    except Exception as exc:  # noqa: BLE001
        print("contact sheet skipped:", exc)

    meta = {
        "fault_code": code,
        "machine": machine_r,
        "n": n,
        "methods": methods_l,
        "outputs": results,
        "out_dir": str(root.resolve()),
        "data_provenance": describe_data_provenance(),
        "note": (
            "procedural/phone use diverse simulated scenes (not black-only). "
            "gan/diffusion only look as diverse as their last training set — "
            "delete old checkpoints under fault_code_gen_artifacts to retrain on new diversity. "
            "increase --diffusion-epochs (50–100+) if diffusion looks noisy."
        ),
    }
    (root / "manifest.json").write_text(json.dumps(meta, indent=2))
    print(json.dumps({k: meta[k] for k in ("fault_code", "machine", "methods", "out_dir")}, indent=2))
    return meta


def _write_contact_sheet(results: dict[str, list[str]], path: Path, size: int = 256) -> None:
    rows = []
    for _method, paths in results.items():
        for p in paths[:4]:
            im = Image.open(p).convert("RGB").resize((size // 2, size // 2))
            rows.append(im)
    if not rows:
        return
    cols = min(4, len(rows))
    n_rows = (len(rows) + cols - 1) // cols
    w = h = size // 2
    sheet = Image.new("RGB", (cols * w, n_rows * h), (30, 30, 30))
    for i, im in enumerate(rows):
        sheet.paste(im, ((i % cols) * w, (i // cols) * h))
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(path)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Generate fault-code images for a machine + code")
    p.add_argument("--code", required=True, help="Fault code, e.g. 5E, UE, F9E1")
    p.add_argument(
        "--machine",
        default=None,
        help="washer|dryer|dishwasher|fridge|generic (default: catalog family)",
    )
    p.add_argument("--n", type=int, default=4, help="Images per method")
    p.add_argument(
        "--methods",
        default="procedural,phone",
        help="Comma list: procedural,phone,gan,diffusion",
    )
    p.add_argument("--out", type=Path, default=Path("notebooks/fault_code_gen_artifacts/requests"))
    p.add_argument("--size", type=int, default=256)
    p.add_argument("--no-auto-train", action="store_true")
    p.add_argument("--gan-epochs", type=int, default=20)
    p.add_argument("--diffusion-epochs", type=int, default=40)
    p.add_argument("--gan-ckpt", type=Path, default=None)
    p.add_argument("--diffusion-ckpt", type=Path, default=None)
    args = p.parse_args(argv)

    generate_images(
        fault_code=args.code,
        machine=args.machine,
        n=args.n,
        methods=args.methods.split(","),
        out_dir=args.out,
        size=args.size,
        auto_train=not args.no_auto_train,
        gan_epochs=args.gan_epochs,
        diffusion_epochs=args.diffusion_epochs,
        gan_ckpt=args.gan_ckpt,
        diffusion_ckpt=args.diffusion_ckpt,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
