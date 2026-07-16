import pandas as pd

checklist = mlops_checklist()
df = pd.DataFrame(checklist)
print(df.to_string(index=False))
df.to_csv(ART / "mlops_checklist.csv", index=False)
print("\nWrote", ART / "mlops_checklist.csv")

# Persist a one-page executive summary for client packs
summary = {
    "title": "Fault-code vision MLOps",
    "production_model": "fault-code-ocr (reader)",
    "offline_factory": "fault-code-gan / procedural seeds",
    "core_diagnosis": "Neo4j GraphRAG (unchanged architecture)",
    "cuda": "Required for official train jobs; optional for inference",
    "promotion_gate": "evals/thresholds.yaml vision_full.real_photo_accuracy",
    "package": "ml/fault_code_vision",
    "lab_notebook": "notebooks/fault_code_gan_synthetic_images.ipynb",
    "this_playbook": "notebooks/fault_code_vision_mlops_playbook.ipynb",
    "registry_aliases": ["fault-code-ocr", "fault-code-gan"],
}
(ART / "executive_summary.json").write_text(json.dumps(summary, indent=2))
print(json.dumps(summary, indent=2))
