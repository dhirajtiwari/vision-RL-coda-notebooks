checklist = [
    "Keep diffusion offline as data factory (not diagnose reasoner)",
    "Condition on closed-set fault-code labels from catalog",
    "Tag source=diffusion_synthetic in manifests",
    "Gate OCR on real photos before production pin",
    "Client train: CUDA + longer epochs / larger UNet or Diffusers LDM",
    "Optional: phone-camera augments after sampling (same as GAN lab)",
]
for i, c in enumerate(checklist, 1):
    print(f"{i}. {c}")

summary = {
    "notebook": "fault_code_diffusion_playbook.ipynb",
    "package": "ml/fault_code_diffusion",
    "method": "class_conditional_DDPM",
    "upgrade": "latent_diffusion_diffusers_controlnet",
    "cuda": "recommended_for_client_quality",
}
(ART / "executive_summary.json").write_text(json.dumps(summary, indent=2))
print(json.dumps(summary, indent=2))
