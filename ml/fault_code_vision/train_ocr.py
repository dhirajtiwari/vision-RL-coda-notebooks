"""Train closed-set fault-code OCR/classifier.

Usage (from repo root):
  python -m ml.fault_code_vision.train_ocr --manifest path.json --epochs 20 --out artifacts/ocr.pt

Client GPU trains should set --require-cuda.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from ml.fault_code_vision.catalog import IDX_TO_CODE, N_CLASSES
from ml.fault_code_vision.dataset import FaultCodeImageDataset, load_manifest, stratified_split
from ml.fault_code_vision.device import assert_cuda_for_client_train, device_report
from ml.fault_code_vision.ocr_model import FaultCodeCNN


def train_one_epoch(model, loader, opt, criterion, device) -> float:
    model.train()
    total, n = 0.0, 0
    for x, y, _codes in loader:
        x, y = x.to(device), y.to(device)
        opt.zero_grad(set_to_none=True)
        logits = model(x)
        loss = criterion(logits, y)
        loss.backward()
        opt.step()
        total += loss.item() * x.size(0)
        n += x.size(0)
    return total / max(n, 1)


@torch.no_grad()
def evaluate(model, loader, device) -> dict:
    model.eval()
    correct, n = 0, 0
    for x, y, _codes in loader:
        x, y = x.to(device), y.to(device)
        pred = model(x).argmax(dim=1)
        correct += (pred == y).sum().item()
        n += y.size(0)
    acc = correct / max(n, 1)
    return {"accuracy": acc, "n": n, "correct": correct}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Train fault-code closed-set classifier")
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--epochs", type=int, default=15)
    p.add_argument("--batch-size", type=int, default=64)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--image-size", type=int, default=64)
    p.add_argument("--out", type=Path, default=Path("notebooks/fault_code_gan_artifacts/checkpoints/ocr.pt"))
    p.add_argument("--require-cuda", action="store_true", help="Fail if CUDA unavailable")
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args(argv)

    torch.manual_seed(args.seed)
    device = assert_cuda_for_client_train(allow_cpu_fallback=not args.require_cuda)
    print("device_report:", json.dumps(device_report(), indent=2))
    print("using device:", device)

    rows = load_manifest(args.manifest)
    # If all rows are seed/synthetic without split, create stratified splits
    if all(r.get("split") in {None, "seed", "synthetic", "train"} for r in rows):
        # keep explicit train rows; re-split seeds for demo
        rows = stratified_split(rows, seed=args.seed)

    train_rows = [r for r in rows if r.get("split") == "train"]
    val_rows = [r for r in rows if r.get("split") == "val"]
    if not train_rows:
        train_rows = rows
    if not val_rows:
        val_rows = train_rows[: max(1, len(train_rows) // 10)]

    train_ds = FaultCodeImageDataset(train_rows, image_size=args.image_size, for_classifier=True)
    val_ds = FaultCodeImageDataset(val_rows, image_size=args.image_size, for_classifier=True)
    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False, num_workers=0)

    model = FaultCodeCNN(n_classes=N_CLASSES).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=args.lr)
    criterion = nn.CrossEntropyLoss()

    best_acc = -1.0
    history = []
    t0 = time.time()
    for epoch in range(1, args.epochs + 1):
        loss = train_one_epoch(model, train_loader, opt, criterion, device)
        metrics = evaluate(model, val_loader, device)
        history.append({"epoch": epoch, "loss": loss, **metrics})
        print(f"[{epoch:03d}/{args.epochs}] loss={loss:.4f} val_acc={metrics['accuracy']:.3f}")
        if metrics["accuracy"] > best_acc:
            best_acc = metrics["accuracy"]
            args.out.parent.mkdir(parents=True, exist_ok=True)
            torch.save(
                {
                    "model": model.state_dict(),
                    "n_classes": N_CLASSES,
                    "idx_to_code": IDX_TO_CODE,
                    "image_size": args.image_size,
                    "val_accuracy": best_acc,
                    "device_report": device_report(),
                },
                args.out,
            )
    print(f"Best val_acc={best_acc:.3f} saved -> {args.out} ({time.time() - t0:.1f}s)")
    metrics_path = args.out.with_suffix(".metrics.json")
    metrics_path.write_text(json.dumps({"best_val_accuracy": best_acc, "history": history}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
