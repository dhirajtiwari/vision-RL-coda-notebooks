"""Dataset manifests and PyTorch Dataset for fault-code images."""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

from PIL import Image
from torch.utils.data import Dataset
from torchvision import transforms

# Manifest schema (one JSON object per image row)
MANIFEST_FIELDS = (
    "path",  # absolute or repo-relative path to PNG/JPEG
    "code",  # ground-truth fault code string
    "class_idx",  # int index into catalog
    "split",  # train | val | test | synthetic | seed
    "source",  # real | synthetic | seed | augment
    "product_id",  # optional product context
    "description",  # optional human text
    "family",  # washer | dryer | ...
)


def load_manifest(path: str | Path) -> list[dict[str, Any]]:
    path = Path(path)
    with path.open() as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Manifest must be a JSON list: {path}")
    return data


def save_manifest(rows: list[dict[str, Any]], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(rows, f, indent=2)


def filter_split(rows: list[dict[str, Any]], split: str) -> list[dict[str, Any]]:
    return [r for r in rows if r.get("split") == split]


def stratified_split(
    rows: list[dict[str, Any]],
    val_frac: float = 0.15,
    test_frac: float = 0.15,
    seed: int = 42,
) -> list[dict[str, Any]]:
    """Assign train/val/test on a copy of rows, stratified by code."""
    rng = random.Random(seed)
    by_code: dict[str, list[dict]] = {}
    for r in rows:
        by_code.setdefault(r["code"], []).append(dict(r))

    out: list[dict[str, Any]] = []
    for _code, items in by_code.items():
        rng.shuffle(items)
        n = len(items)
        n_test = max(1, int(n * test_frac)) if n >= 5 else 0
        n_val = max(1, int(n * val_frac)) if n >= 5 else 0
        for i, row in enumerate(items):
            if i < n_test:
                row["split"] = "test"
            elif i < n_test + n_val:
                row["split"] = "val"
            else:
                row["split"] = "train"
            out.append(row)
    return out


class FaultCodeImageDataset(Dataset):
    """RGB images normalized to [-1, 1] (compatible with Tanh generators) or [0,1] classify."""

    def __init__(
        self,
        meta: list[dict[str, Any]],
        image_size: int = 64,
        for_classifier: bool = True,
        online_aug: bool = False,
    ):
        self.meta = meta
        self.online_aug = online_aug
        if for_classifier:
            self.tf = transforms.Compose(
                [
                    transforms.Resize((image_size, image_size)),
                    transforms.ToTensor(),
                    transforms.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225)),
                ]
            )
        else:
            self.tf = transforms.Compose(
                [
                    transforms.Resize((image_size, image_size)),
                    transforms.ToTensor(),
                    transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
                ]
            )

    def __len__(self) -> int:
        return len(self.meta)

    def __getitem__(self, idx: int):
        row = self.meta[idx]
        img = Image.open(row["path"]).convert("RGB")
        x = self.tf(img)
        y = int(row["class_idx"])
        return x, y, row["code"]
