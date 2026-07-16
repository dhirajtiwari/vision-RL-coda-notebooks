"""Inference: image -> fault code (closed-set) for GraphRAG ingress."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import torch
from PIL import Image
from torchvision import transforms

from ml.fault_code_vision.catalog import IDX_TO_CODE, is_closed_set_code
from ml.fault_code_vision.device import pick_device
from ml.fault_code_vision.ocr_model import FaultCodeCNN


def _tf(image_size: int = 64):
    return transforms.Compose(
        [
            transforms.Resize((image_size, image_size)),
            transforms.ToTensor(),
            transforms.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225)),
        ]
    )


class FaultCodeReader:
    """Load a pinned OCR checkpoint and predict closed-set codes."""

    def __init__(self, checkpoint: str | Path, device: torch.device | None = None):
        self.device = device or pick_device()
        ckpt = torch.load(checkpoint, map_location=self.device, weights_only=False)
        self.idx_to_code = {int(k): v for k, v in ckpt.get("idx_to_code", IDX_TO_CODE).items()}
        self.image_size = int(ckpt.get("image_size", 64))
        n_classes = int(ckpt.get("n_classes", len(self.idx_to_code)))
        self.model = FaultCodeCNN(n_classes=n_classes).to(self.device)
        self.model.load_state_dict(ckpt["model"])
        self.model.eval()
        self.tf = _tf(self.image_size)
        self.checkpoint = str(checkpoint)
        self.val_accuracy = ckpt.get("val_accuracy")

    @torch.no_grad()
    def predict(self, image: Image.Image | str | Path, min_confidence: float = 0.0) -> dict[str, Any]:
        if not isinstance(image, Image.Image):
            image = Image.open(image).convert("RGB")
        else:
            image = image.convert("RGB")
        x = self.tf(image).unsqueeze(0).to(self.device)
        logits = self.model(x)
        probs = torch.softmax(logits, dim=1)[0]
        conf, idx = probs.max(dim=0)
        code = self.idx_to_code[int(idx.item())]
        confidence = float(conf.item())
        ok = confidence >= min_confidence and is_closed_set_code(code)
        return {
            "code": code if ok else None,
            "raw_code": code,
            "confidence": confidence,
            "accepted": ok,
            "model_checkpoint": self.checkpoint,
            "model_val_accuracy": self.val_accuracy,
            "escalate": not ok,
        }


def user_message_for_graph_rag(code: str) -> str:
    """Format that graph_rag.match_error_codes can consume via substring match."""
    return f"Customer uploaded display photo. Error code {code} shown on machine."
