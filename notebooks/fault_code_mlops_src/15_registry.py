import yaml

reg_path = ROOT / "models" / "registry.yaml"
reg = yaml.safe_load(reg_path.read_text())
vision_aliases = {k: v for k, v in reg.get("models", {}).items() if k.startswith("fault-code")}
print("Vision registry stubs:")
print(yaml.dump(vision_aliases, sort_keys=False))

thr = yaml.safe_load((ROOT / "evals" / "thresholds.yaml").read_text())
print("Vision floors:")
print(yaml.dump({k: thr[k] for k in thr if k.startswith("vision")}, sort_keys=False))

# FinOps-style unit costs (illustrative — wire to finops/ when serving)
finops_sketch = {
    "train_gpu_hour_usd": 1.5,
    "infer_cpu_per_1k_images_usd": 0.05,
    "infer_gpu_per_1k_images_usd": 0.40,
    "daily_budget_usd_suggestion": 25.0,
    "metrics": [
        "ocr_requests_total",
        "ocr_latency_seconds",
        "ocr_confidence",
        "ocr_unknown_or_low_conf_total",
        "ocr_model_version",
    ],
}
print("FinOps / metrics sketch:")
print(json.dumps(finops_sketch, indent=2))
(ART / "finops_metrics_sketch.json").write_text(json.dumps(finops_sketch, indent=2))
