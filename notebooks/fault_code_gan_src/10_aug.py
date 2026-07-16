def _random_glare(img: Image.Image) -> Image.Image:
    arr = np.array(img).astype(np.float32)
    h, w, _ = arr.shape
    cy, cx = random.uniform(0.2, 0.8) * h, random.uniform(0.2, 0.8) * w
    yy, xx = np.mgrid[0:h, 0:w]
    sigma = random.uniform(w * 0.08, w * 0.22)
    blob = np.exp(-((yy - cy) ** 2 + (xx - cx) ** 2) / (2 * sigma**2))
    strength = random.uniform(40, 120)
    arr = np.clip(arr + (blob * strength)[..., None], 0, 255)
    return Image.fromarray(arr.astype(np.uint8))


def phone_camera_augment(img: Image.Image) -> Image.Image:
    """Map clean LCD seed to claim-photo-like crop."""
    out = img.convert("RGB")

    if random.random() < 0.9:
        out = out.rotate(random.uniform(-18, 18), resample=Image.BICUBIC, fillcolor=(30, 30, 30))

    if random.random() < 0.7:
        w, h = out.size
        dx = random.uniform(-0.08, 0.08) * w
        dy = random.uniform(-0.08, 0.08) * h
        out = out.transform(
            out.size,
            Image.AFFINE,
            (1, random.uniform(-0.12, 0.12), dx, random.uniform(-0.12, 0.12), 1, dy),
            resample=Image.BICUBIC,
            fillcolor=(25, 25, 25),
        )

    out = ImageEnhance.Brightness(out).enhance(random.uniform(0.55, 1.35))
    out = ImageEnhance.Contrast(out).enhance(random.uniform(0.7, 1.5))
    out = ImageEnhance.Color(out).enhance(random.uniform(0.6, 1.3))

    if random.random() < 0.55:
        out = out.filter(ImageFilter.GaussianBlur(radius=random.uniform(0.4, 1.8)))

    if random.random() < 0.45:
        out = _random_glare(out)

    if random.random() < 0.7:
        arr = np.array(out).astype(np.float32)
        noise = np.random.normal(0, random.uniform(4, 18), arr.shape)
        out = Image.fromarray(np.clip(arr + noise, 0, 255).astype(np.uint8))

    if random.random() < 0.5:
        w, h = out.size
        scale = random.uniform(0.75, 0.95)
        nw, nh = int(w * scale), int(h * scale)
        left = random.randint(0, w - nw)
        top = random.randint(0, h - nh)
        out = out.crop((left, top, left + nw, top + nh)).resize((w, h), Image.BICUBIC)

    if random.random() < 0.25:
        out = ImageOps.posterize(out, bits=random.randint(5, 7))

    return out


demo = render_lcd_panel("5E", style="lcd_dark", size=IMG_SIZE)
fig, axes = plt.subplots(2, 6, figsize=(11, 4))
axes[0, 0].imshow(demo)
axes[0, 0].set_title("seed")
axes[0, 0].axis("off")
for i in range(1, 12):
    r, c = divmod(i, 6)
    axes[r, c].imshow(phone_camera_augment(demo))
    axes[r, c].axis("off")
    axes[r, c].set_title(f"aug {i}")
plt.suptitle("Classical claim-photo augmentations of seed '5E'")
plt.tight_layout()
plt.savefig(ART / "preview_augments.png", dpi=120)
plt.show()
