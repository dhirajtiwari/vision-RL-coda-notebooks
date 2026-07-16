# Full control-panel seeds (readable digits). Under-trained DDPM ≈ pure noise.
# For crisp on-demand images without long train:
#   notebooks/fault_code_image_generator.ipynb  (methods procedural, phone)
from ml.fault_code_vision.cgan import build_panel_manifest

manifest = build_panel_manifest(ART / "panel_data", n_per_code=24, size=64)
print("panel manifest", manifest)

EPOCHS = 40  # 60–100 on CUDA for readable digits; short runs stay noisy
result = train_ddpm(
    manifest,
    ART,
    DDPMConfig(T=200, epochs=EPOCHS, batch_size=32, require_cuda=False),
)
print("checkpoint:", result["ckpt_path"])

hist = result["history"]
plt.figure(figsize=(7, 3))
plt.plot([h["epoch"] for h in hist], [h["loss"] for h in hist])
plt.xlabel("epoch")
plt.ylabel("noise MSE")
plt.title("DDPM training loss")
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(ART / "ddpm_loss.png", dpi=120)
plt.show()
