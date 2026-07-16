def build_seed_corpus(
    n_per_code: int = 40,
    size: int = IMG_SIZE,
    out_dir: Path = SEED_DIR,
) -> list[dict]:
    """Create labelled seed images on disk. Returns metadata rows."""
    meta: list[dict] = []
    out_dir.mkdir(parents=True, exist_ok=True)
    for p in out_dir.glob("*.png"):
        p.unlink()

    for row in FAULT_CATALOG:
        code = row["code"]
        for i in range(n_per_code):
            style = STYLES[i % len(STYLES)]
            img = render_lcd_panel(code, style=style, size=size)
            factor = random.uniform(0.85, 1.15)
            img = ImageEnhance.Brightness(img).enhance(factor)
            fname = f"{code}__{style}__{i:03d}.png"
            path = out_dir / fname
            img.save(path)
            meta.append(
                {
                    "path": str(path),
                    "code": code,
                    "class_idx": CODE_TO_IDX[code],
                    "style": style,
                    "description": row["description"],
                    "family": row["family"],
                    "split": "seed",
                }
            )
    with open(ART / "seed_manifest.json", "w") as f:
        json.dump(meta, f, indent=2)
    print(f"Wrote {len(meta)} seed images -> {out_dir}")
    return meta


seed_meta = build_seed_corpus(n_per_code=48)
print("Example:", seed_meta[0])
