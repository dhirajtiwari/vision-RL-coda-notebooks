"""Orchestration helpers: seed data -> train OCR -> eval -> diagnose payload."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ml.fault_code_vision.dataset import save_manifest, stratified_split
from ml.fault_code_vision.seed_render import build_seed_corpus


def bootstrap_demo_dataset(
    art_dir: str | Path,
    n_per_code: int = 24,
    image_size: int = 64,
) -> Path:
    """Create seed LCD images + stratified manifest for local/CUDA smoke trains."""
    art_dir = Path(art_dir)
    art_dir.mkdir(parents=True, exist_ok=True)
    seed_dir = art_dir / "seed_lcd"
    rows = build_seed_corpus(seed_dir, n_per_code=n_per_code, size=image_size)
    rows = stratified_split(rows)
    man = art_dir / "ocr_train_manifest.json"
    save_manifest(rows, man)
    meta = {
        "n_images": len(rows),
        "n_per_code": n_per_code,
        "image_size": image_size,
        "manifest": str(man),
        "note": "Synthetic seeds only — not a real-photo promotion gate",
    }
    (art_dir / "dataset_meta.json").write_text(json.dumps(meta, indent=2))
    return man


def mlops_checklist() -> list[dict[str, Any]]:
    """Static checklist for client delivery (also rendered in the playbook notebook)."""
    return [
        {
            "phase": 0,
            "item": "Charter: OCR is production model; GAN is data factory; GraphRAG core",
            "status": "required",
        },
        {"phase": 0, "item": "Success metrics + real-photo hold-out gate defined with client", "status": "required"},
        {"phase": 1, "item": "CUDA VM: nvidia-smi, torch.cuda.is_available(), Dockerfile.gpu", "status": "required"},
        {
            "phase": 2,
            "item": "Dataset versioning (manifest + object store + source=real|synthetic)",
            "status": "required",
        },
        {"phase": 2, "item": "Collect first real claim display photos for hold-out", "status": "required"},
        {"phase": 3, "item": "Train OCR/classifier; track runs (MLflow/W&B optional)", "status": "required"},
        {"phase": 3, "item": "Eval floors on synthetic + real; never promote synthetic-only", "status": "required"},
        {"phase": 4, "item": "Pin model in models/registry.yaml; checksum artifact", "status": "required"},
        {"phase": 4, "item": "CI/nightly vision eval gate before registry flip", "status": "required"},
        {
            "phase": 5,
            "item": "API: multipart upload -> OCR -> match_error_codes / structured codes",
            "status": "required",
        },
        {"phase": 5, "item": "Closed-set filter to product HAS_ERROR_CODE list", "status": "required"},
        {"phase": 5, "item": "Low confidence escalate; provenance model_version on response", "status": "required"},
        {"phase": 6, "item": "Prometheus: ocr latency, confidence, unknown rate", "status": "required"},
        {"phase": 6, "item": "FinOps: GPU train cost + per-image inference cost", "status": "recommended"},
        {"phase": 6, "item": "PII retention, malware scan, authz on uploads", "status": "required"},
        {"phase": 6, "item": "Model card + AI-BOM entry; retrain on new OEM codes", "status": "required"},
    ]
