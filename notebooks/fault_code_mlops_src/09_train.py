from ml.fault_code_vision.train_ocr import main as train_ocr_main

ckpt_path = CKPT_DIR / "fault_code_ocr_playbook.pt"
# Interactive notebook default; raise to 20–40 + --require-cuda on client GPU
rc = train_ocr_main([
    "--manifest", str(manifest_path),
    "--epochs", "12",
    "--batch-size", "64",
    "--lr", "0.002",
    "--out", str(ckpt_path),
    # omit --require-cuda so local MPS/CPU works; add it on client GPU jobs
])
print("train exit code:", rc)
print("checkpoint:", ckpt_path, "exists=", ckpt_path.exists())
if ckpt_path.with_suffix(".metrics.json").exists():
    print(ckpt_path.with_suffix(".metrics.json").read_text()[:500], "...")
