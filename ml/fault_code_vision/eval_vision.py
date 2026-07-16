"""Vision eval harness — accuracy floors for OCR promotion.

Usage:
  python -m ml.fault_code_vision.eval_vision \\
    --checkpoint artifacts/ocr.pt \\
    --manifest path/to/test_manifest.json \\
    --min-accuracy 0.85
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image

from ml.fault_code_vision.dataset import load_manifest
from ml.fault_code_vision.infer import FaultCodeReader


def evaluate_checkpoint(
    checkpoint: str | Path,
    manifest: str | Path,
    min_confidence: float = 0.0,
    split: str | None = "test",
) -> dict:
    rows = load_manifest(manifest)
    if split:
        filtered = [r for r in rows if r.get("split") == split]
        if filtered:
            rows = filtered
        else:
            # Fallback so notebooks never crash if split is missing
            for alt in ("val", "train", "seed", None):
                if alt is None:
                    break
                filtered = [r for r in rows if r.get("split") == alt]
                if filtered:
                    rows = filtered
                    break
    if not rows:
        return {"n": 0, "correct": 0, "accuracy": 0.0, "checkpoint": str(checkpoint), "details": []}
    reader = FaultCodeReader(checkpoint)
    details = []
    correct = 0
    for row in rows:
        pred = reader.predict(Image.open(row["path"]), min_confidence=min_confidence)
        ok = pred.get("code") == row["code"]
        correct += int(ok)
        details.append(
            {
                "truth": row["code"],
                "pred": pred.get("code"),
                "confidence": pred.get("confidence"),
                "ok": ok,
                "path": row["path"],
            }
        )
    n = len(rows)
    acc = correct / max(n, 1)
    return {
        "n": n,
        "correct": correct,
        "accuracy": acc,
        "checkpoint": str(checkpoint),
        "details": details,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--checkpoint", type=Path, required=True)
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--min-accuracy", type=float, default=0.80)
    p.add_argument("--min-confidence", type=float, default=0.0)
    p.add_argument("--split", type=str, default="test")
    p.add_argument("--report", type=Path, default=None)
    args = p.parse_args(argv)

    report = evaluate_checkpoint(
        args.checkpoint,
        args.manifest,
        min_confidence=args.min_confidence,
        split=args.split if args.split else None,
    )
    summary = {k: report[k] for k in ("n", "correct", "accuracy", "checkpoint")}
    print(json.dumps(summary, indent=2))
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2))
        print("wrote", args.report)

    if report["accuracy"] < args.min_accuracy:
        print(f"FAIL: accuracy {report['accuracy']:.3f} < floor {args.min_accuracy:.3f}")
        return 1
    print(f"PASS: accuracy {report['accuracy']:.3f} >= {args.min_accuracy:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
