IMG_SIZE = 64  # DCGAN-friendly; increase to 128 if you have more train time / GPU


def _load_font(size: int) -> ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Courier New Bold.ttf",
        "/System/Library/Fonts/Supplemental/Courier New.ttf",
        "/Library/Fonts/Courier New.ttf",
        "/System/Library/Fonts/Monaco.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
        "DejaVuSansMono-Bold.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def render_lcd_panel(code: str, style: str = "lcd_dark", size: int = IMG_SIZE) -> Image.Image:
    """Render a single fault code as an appliance display crop."""
    code = code.upper()
    img = Image.new("RGB", (size, size))
    draw = ImageDraw.Draw(img)

    if style == "lcd_dark":
        bg, fg, bezel = (18, 28, 22), (140, 200, 120), (40, 40, 40)
    elif style == "lcd_blue":
        bg, fg, bezel = (10, 20, 50), (80, 160, 255), (30, 30, 45)
    elif style == "led_red":
        bg, fg, bezel = (8, 8, 8), (255, 40, 40), (20, 20, 20)
    elif style == "led_amber":
        bg, fg, bezel = (12, 10, 5), (255, 170, 40), (25, 22, 15)
    elif style == "oled_white":
        bg, fg, bezel = (5, 5, 5), (230, 230, 230), (15, 15, 15)
    else:
        bg, fg, bezel = (18, 28, 22), (140, 200, 120), (40, 40, 40)

    draw.rectangle([0, 0, size - 1, size - 1], fill=bezel)
    margin = max(4, size // 12)
    draw.rounded_rectangle(
        [margin, margin, size - 1 - margin, size - 1 - margin],
        radius=size // 16,
        fill=bg,
    )

    for y in range(margin + 2, size - margin - 2, 2):
        alpha = 8 if style.startswith("lcd") else 4
        draw.line(
            [(margin + 2, y), (size - margin - 3, y)],
            fill=tuple(min(255, c + alpha) for c in bg),
        )

    font_size = max(14, size // (2 if len(code) <= 2 else 3))
    font = _load_font(font_size)

    bbox = draw.textbbox((0, 0), code, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (size - tw) // 2 - bbox[0]
    y = (size - th) // 2 - bbox[1] - size // 32
    if style.startswith("led"):
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1)]:
            draw.text((x + dx, y + dy), code, font=font, fill=tuple(c // 3 for c in fg))
    draw.text((x, y), code, font=font, fill=fg)

    if style in {"lcd_dark", "lcd_blue"} and size >= 64:
        small = _load_font(max(8, size // 10))
        label = "ERROR"
        bb = draw.textbbox((0, 0), label, font=small)
        lw = bb[2] - bb[0]
        draw.text(
            ((size - lw) // 2, margin + 2),
            label,
            font=small,
            fill=tuple(c // 2 for c in fg),
        )

    return img


STYLES = ["lcd_dark", "lcd_blue", "led_red", "led_amber", "oled_white"]

fig, axes = plt.subplots(len(STYLES), 6, figsize=(10, 8))
sample_codes = [FAULT_CATALOG[i]["code"] for i in range(6)]
for r, style in enumerate(STYLES):
    for c, code in enumerate(sample_codes):
        axes[r, c].imshow(render_lcd_panel(code, style=style, size=IMG_SIZE))
        axes[r, c].axis("off")
        if r == 0:
            axes[r, c].set_title(code, fontsize=9)
    axes[r, 0].set_ylabel(style, fontsize=8)
plt.suptitle("Procedural seed displays (domain fault codes)")
plt.tight_layout()
plt.savefig(ART / "preview_seed_styles.png", dpi=120)
plt.show()
print("Saved", ART / "preview_seed_styles.png")
