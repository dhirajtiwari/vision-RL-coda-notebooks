def materialize_augmented(
    seed_meta: list[dict],
    n_aug_per_seed: int = 3,
    out_dir: Path = AUG_DIR,
) -> list[dict]:
    out_dir.mkdir(parents=True, exist_ok=True)
    for p in out_dir.glob("*.png"):
        p.unlink()
    rows: list[dict] = []
    for s in seed_meta:
        base = Image.open(s["path"]).convert("RGB")
        dest = out_dir / Path(s["path"]).name
        base.save(dest)
        rows.append({**s, "path": str(dest), "split": "train", "source": "seed"})
        for j in range(n_aug_per_seed):
            aug = phone_camera_augment(base)
            fname = f"{s['code']}__aug__{Path(s['path']).stem}__{j}.png"
            path = out_dir / fname
            aug.save(path)
            rows.append(
                {
                    **{k: s[k] for k in ("code", "class_idx", "description", "family")},
                    "path": str(path),
                    "style": s.get("style", "aug"),
                    "split": "train",
                    "source": "augment",
                }
            )
    with open(ART / "train_manifest.json", "w") as f:
        json.dump(rows, f, indent=2)
    print(f"Train corpus: {len(rows)} images ({len(seed_meta)} seeds x ~{1 + n_aug_per_seed})")
    return rows


train_meta = materialize_augmented(seed_meta, n_aug_per_seed=2)


class FaultCodeDataset(Dataset):
    """Loads RGB images -> tensor in [-1, 1] for Tanh generators."""

    def __init__(self, meta: list[dict], image_size: int = IMG_SIZE, online_aug: bool = False):
        self.meta = meta
        self.online_aug = online_aug
        self.tf = transforms.Compose(
            [
                transforms.Resize((image_size, image_size)),
                transforms.ToTensor(),
                transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
            ]
        )

    def __len__(self) -> int:
        return len(self.meta)

    def __getitem__(self, idx: int):
        row = self.meta[idx]
        img = Image.open(row["path"]).convert("RGB")
        if self.online_aug and random.random() < 0.5:
            img = phone_camera_augment(img)
        x = self.tf(img)
        y = int(row["class_idx"])
        return x, y, row["code"]


dataset = FaultCodeDataset(train_meta, image_size=IMG_SIZE, online_aug=True)
loader = DataLoader(dataset, batch_size=64, shuffle=True, num_workers=0, drop_last=True)
print(f"Dataset size={len(dataset)} | batches/epoch={len(loader)}")
xb, yb, codes = next(iter(loader))
print("batch", xb.shape, yb[:8].tolist(), codes[:8])
