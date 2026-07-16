@torch.no_grad()
def generate_synthetic_corpus(
    n_per_code: int = 20,
    out_dir: Path | None = None,
    post_augment: bool = True,
) -> list[dict]:
    out_dir = out_dir or (GEN_DIR / "corpus")
    out_dir.mkdir(parents=True, exist_ok=True)
    for p in out_dir.glob("*.png"):
        p.unlink()

    Gc.eval()
    rows: list[dict] = []
    for class_idx, code in IDX_TO_CODE.items():
        z = torch.randn(n_per_code, NZ, 1, 1, device=DEVICE)
        y = torch.full((n_per_code,), class_idx, device=DEVICE, dtype=torch.long)
        fakes = Gc(z, y).cpu()
        fakes = (fakes * 0.5 + 0.5).clamp(0, 1)
        for j in range(n_per_code):
            t = fakes[j]
            img = transforms.ToPILImage()(t)
            if post_augment:
                img = phone_camera_augment(img.resize((IMG_SIZE, IMG_SIZE), Image.BICUBIC))
            fname = f"synth__{code}__{j:03d}.png"
            path = out_dir / fname
            img.save(path)
            rows.append(
                {
                    "path": str(path),
                    "code": code,
                    "class_idx": class_idx,
                    "description": FAULT_CATALOG[class_idx]["description"],
                    "family": FAULT_CATALOG[class_idx]["family"],
                    "split": "synthetic",
                    "source": "cgan+phone_aug" if post_augment else "cgan",
                }
            )
    man = ART / "synthetic_corpus_manifest.json"
    with open(man, "w") as f:
        json.dump(rows, f, indent=2)
    print(f"Synthetic corpus: {len(rows)} images -> {out_dir}")
    print(f"Manifest: {man}")
    return rows


synth_meta = generate_synthetic_corpus(n_per_code=12, post_augment=True)

fig, axes = plt.subplots(2, 8, figsize=(12, 3.5))
for ax, row in zip(axes.ravel(), synth_meta[:16]):
    ax.imshow(Image.open(row["path"]))
    ax.set_title(row["code"], fontsize=8)
    ax.axis("off")
plt.suptitle("Synthetic claim-style fault-code images (cGAN + phone aug)")
plt.tight_layout()
plt.savefig(ART / "preview_synthetic_corpus.png", dpi=120)
plt.show()
