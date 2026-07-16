"""Procedural LCD/LED seed images for bootstrap when real claim photos are sparse."""

from __future__ import annotations

import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFont

from ml.fault_code_vision.catalog import CODE_TO_IDX, FAULT_CATALOG

STYLES = ["lcd_dark", "lcd_blue", "led_red", "led_amber", "oled_white"]


def _load_font(size: int) -> ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Courier New Bold.ttf",
        "/System/Library/Fonts/Supplemental/Courier New.ttf",
        "/Library/Fonts/Courier New.ttf",
        "/System/Library/Fonts/Monaco.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def render_lcd_panel(code: str, style: str = "lcd_dark", size: int = 64) -> Image.Image:
    code = code.upper()
    img = Image.new("RGB", (size, size))
    draw = ImageDraw.Draw(img)

    palettes = {
        "lcd_dark": ((18, 28, 22), (140, 200, 120), (40, 40, 40)),
        "lcd_blue": ((10, 20, 50), (80, 160, 255), (30, 30, 45)),
        "led_red": ((8, 8, 8), (255, 40, 40), (20, 20, 20)),
        "led_amber": ((12, 10, 5), (255, 170, 40), (25, 22, 15)),
        "oled_white": ((5, 5, 5), (230, 230, 230), (15, 15, 15)),
    }
    bg, fg, bezel = palettes.get(style, palettes["lcd_dark"])

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

    font = _load_font(max(14, size // (2 if len(code) <= 2 else 3)))
    bbox = draw.textbbox((0, 0), code, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (size - tw) // 2 - bbox[0]
    y = (size - th) // 2 - bbox[1] - size // 32
    if style.startswith("led"):
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            draw.text((x + dx, y + dy), code, font=font, fill=tuple(c // 3 for c in fg))
    draw.text((x, y), code, font=font, fill=fg)
    return img


def build_seed_corpus(
    out_dir: str | Path,
    n_per_code: int = 24,
    size: int = 64,
    product_id: str = "wm-001",
) -> list[dict]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for p in out_dir.glob("*.png"):
        p.unlink()

    meta: list[dict] = []
    for row in FAULT_CATALOG:
        code = row["code"]
        for i in range(n_per_code):
            style = STYLES[i % len(STYLES)]
            img = render_lcd_panel(code, style=style, size=size)
            img = ImageEnhance.Brightness(img).enhance(random.uniform(0.85, 1.15))
            path = out_dir / f"{code}__{style}__{i:03d}.png"
            img.save(path)
            meta.append(
                {
                    "path": str(path.resolve()),
                    "code": code,
                    "class_idx": CODE_TO_IDX[code],
                    "style": style,
                    "description": row["description"],
                    "family": row["family"],
                    "product_id": product_id,
                    "split": "seed",
                    "source": "seed",
                }
            )
    return meta
