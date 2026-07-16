try:
    from IPython.display import display
except ImportError:
    def display(x):
        return None

codes = ["5E", "UE", "E24", "F9E1", "4E", "DE"]
paths = generate_codes(result["ckpt_path"], codes, ART / "generated", n_per_code=3)
print(f"wrote {len(paths)} images ->", ART / "generated")

fig, axes = plt.subplots(len(codes), 3, figsize=(6, 10))
for i, code in enumerate(codes):
    for j in range(3):
        p = ART / "generated" / f"diff__{code}__{j:03d}.png"
        if p.exists():
            axes[i, j].imshow(Image.open(p))
        axes[i, j].axis("off")
        if j == 0:
            axes[i, j].set_ylabel(code)
plt.suptitle("Conditional DDPM samples (quality rises with more epochs / CUDA)")
plt.tight_layout()
plt.savefig(ART / "preview_diffusion_grid.png", dpi=120)
plt.show()

samples = sorted((ART / "samples").glob("epoch_*.png"))
if samples:
    print("training snapshot:", samples[-1])
    display(Image.open(samples[-1]))
else:
    print("No training sample grids found yet.")
