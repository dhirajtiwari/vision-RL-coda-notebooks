# Bootstrap a small stratified seed dataset for OCR train (dev proxy)
manifest_path = bootstrap_demo_dataset(ART / "dataset", n_per_code=24, image_size=64)
rows = load_manifest(manifest_path)
from collections import Counter
print("Manifest:", manifest_path)
print("N=", len(rows), "splits=", Counter(r["split"] for r in rows))
print("codes sample:", sorted({r["code"] for r in rows})[:8], "...")

# Preview a few seeds
fig, axes = plt.subplots(2, 6, figsize=(10, 3.5))
for ax, row in zip(axes.ravel(), rows[:12]):
    ax.imshow(Image.open(row["path"]))
    ax.set_title(f"{row['code']}/{row['split']}", fontsize=8)
    ax.axis("off")
plt.suptitle("Bootstrap seed displays for OCR training")
plt.tight_layout()
plt.savefig(ART / "preview_bootstrap.png", dpi=120)
plt.show()
