"""Diverse appliance fault-display images for training + demos.

IMPORTANT — where training data comes from
------------------------------------------
We do **not** load real customer claim photos (client has few/none).
All labels are **procedurally simulated** to mimic real claim scenarios.
GAN/diffusion therefore learn *only* the distribution we synthesize here.
If every seed is a dark LCD on black, models reproduce dark-on-black forever.

Real claim-photo factors we now randomize
-----------------------------------------
  • Room backdrop (laundry wall, kitchen, tile, wood, concrete, window light)
  • Appliance finish (white, stainless, black, graphite, beige)
  • Display type (green LCD, blue LCD, red LED, amber, white OLED, **gray LCD + black ink**)
  • Framing (tight LCD crop, full control panel, machine-in-room wide shot)
  • Lighting / phone camera degradations
"""

from __future__ import annotations

import random
from typing import Any, Literal

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

Machine = Literal["washer", "dryer", "dishwasher", "fridge", "generic"]

# Chassis finishes seen in the field (not only dark graphite)
BODY_FINISHES: dict[str, tuple[int, int, int]] = {
    "white": (242, 242, 245),
    "off_white": (230, 228, 220),
    "stainless": (178, 182, 188),
    "silver": (160, 165, 172),
    "black": (28, 28, 32),
    "graphite": (52, 58, 66),
    "beige": (210, 200, 180),
    "navy": (35, 45, 70),
}

# Room / environment backdrops (claim photo context)
SCENE_BACKDROPS = (
    "laundry_beige",
    "laundry_blue",
    "kitchen_white",
    "kitchen_warm",
    "tile_gray",
    "wood_floor",
    "concrete",
    "garage",
    "window_bright",
    "evening_warm",
)

DISPLAY_STYLES = (
    "lcd_green",  # classic dark green LCD
    "lcd_blue",
    "lcd_gray_black",  # light segment panel + black digits (very common)
    "lcd_gray_blue",
    "led_red",
    "led_amber",
    "oled_white",
    "vfd_cyan",  # vacuum fluorescent style
)

MACHINE_THEMES: dict[str, dict[str, Any]] = {
    "washer": {
        "label": "WASHER",
        "accents": [(0, 120, 200), (20, 90, 160), (0, 150, 140)],
        "finishes": ["white", "stainless", "graphite", "black", "silver"],
        "styles": ["lcd_green", "lcd_gray_black", "lcd_blue", "led_amber"],
    },
    "dryer": {
        "label": "DRYER",
        "accents": [(220, 90, 30), (180, 60, 20), (100, 100, 110)],
        "finishes": ["white", "graphite", "stainless", "beige"],
        "styles": ["led_amber", "lcd_gray_black", "oled_white", "lcd_green"],
    },
    "dishwasher": {
        "label": "DISHWASHER",
        "accents": [(40, 160, 180), (30, 100, 140), (80, 80, 90)],
        "finishes": ["stainless", "white", "black", "silver"],
        "styles": ["lcd_blue", "lcd_gray_black", "led_red", "vfd_cyan"],
    },
    "fridge": {
        "label": "REFRIGERATOR",
        "accents": [(30, 30, 35), (60, 60, 70), (0, 100, 160)],
        "finishes": ["white", "stainless", "black", "off_white"],
        "styles": ["oled_white", "lcd_blue", "lcd_gray_black", "led_red"],
    },
    "generic": {
        "label": "APPLIANCE",
        "accents": [(100, 100, 110), (0, 120, 200), (180, 80, 40)],
        "finishes": ["white", "graphite", "stainless", "black"],
        "styles": list(DISPLAY_STYLES),
    },
}


def _font(size: int) -> ImageFont.ImageFont:
    for path in (
        "/System/Library/Fonts/Supplemental/Courier New Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ):
        try:
            return ImageFont.truetype(path, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def _lcd_colors(style: str) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
    palettes = {
        "lcd_green": ((18, 32, 22), (120, 230, 110)),
        "lcd_dark": ((18, 28, 22), (140, 220, 120)),
        "lcd_blue": ((12, 24, 55), (90, 170, 255)),
        "lcd_gray_black": ((200, 205, 195), (20, 25, 20)),  # light glass, dark ink
        "lcd_gray_blue": ((190, 200, 210), (15, 40, 90)),
        "led_red": ((12, 8, 8), (255, 55, 45)),
        "led_amber": ((18, 12, 6), (255, 175, 45)),
        "oled_white": ((8, 8, 10), (245, 245, 250)),
        "vfd_cyan": ((5, 15, 20), (40, 230, 220)),
    }
    return palettes.get(style, palettes["lcd_green"])


def _scene_background(size: int, scene: str, rng: random.Random) -> Image.Image:
    """Synthetic room backdrop (not a real photo dataset)."""
    arr = np.zeros((size, size, 3), dtype=np.float32)
    yy, xx = np.mgrid[0:size, 0:size]
    yn, xn = yy / size, xx / size

    if scene == "laundry_beige":
        base = np.array([210, 200, 185], dtype=np.float32)
        arr[:] = base + (yn * 15)[..., None]
        # wall wainscot band
        arr[int(size * 0.55) :, :] = np.array([180, 175, 165], dtype=np.float32)
    elif scene == "laundry_blue":
        arr[:] = np.array([170, 190, 210], dtype=np.float32) + (xn * 20 - 10)[..., None]
    elif scene == "kitchen_white":
        arr[:] = 235
        # cabinet band
        arr[: int(size * 0.25), :] = np.array([250, 250, 252], dtype=np.float32)
        arr[int(size * 0.7) :, :] = np.array([200, 195, 185], dtype=np.float32)  # counter
    elif scene == "kitchen_warm":
        arr[:] = np.array([240, 220, 190], dtype=np.float32)
        arr[int(size * 0.65) :, :] = np.array([120, 80, 50], dtype=np.float32)  # wood
    elif scene == "tile_gray":
        arr[:] = 190
        tile = max(8, size // 12)
        for i in range(0, size, tile):
            arr[i : i + 1, :] *= 0.85
            arr[:, i : i + 1] *= 0.85
    elif scene == "wood_floor":
        arr[:] = np.array([160, 120, 70], dtype=np.float32)
        for i in range(0, size, max(4, size // 20)):
            arr[:, i : i + 2] *= 0.9
    elif scene == "concrete":
        noise = np.random.RandomState(rng.randint(0, 10_000)).randint(0, 25, size=(size, size, 1))
        arr[:] = 140 + noise
    elif scene == "garage":
        arr[:] = np.array([100, 105, 110], dtype=np.float32)
        arr[int(size * 0.6) :, :] = np.array([80, 80, 85], dtype=np.float32)
    elif scene == "window_bright":
        # bright window gradient left
        arr[:] = np.array([220, 225, 230], dtype=np.float32)
        glow = np.clip(1.0 - xn * 1.2, 0, 1)[..., None] * 50
        arr += glow
    else:  # evening_warm
        arr[:] = np.array([80, 60, 50], dtype=np.float32)
        arr += (1.0 - yn)[..., None] * np.array([40, 20, 10])

    # soft vertical shadow / uneven room light
    arr *= 0.85 + 0.2 * (1.0 - xn)[..., None]
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)


def render_lcd_module(
    code: str,
    style: str,
    width: int,
    height: int,
    rng: random.Random,
) -> Image.Image:
    """Just the display glass with fault code."""
    bg, fg = _lcd_colors(style)
    lcd = Image.new("RGB", (width, height), bg)
    draw = ImageDraw.Draw(lcd)
    # inner bezel
    draw.rectangle([0, 0, width - 1, height - 1], outline=tuple(max(0, c - 40) for c in bg), width=2)
    if style.startswith("lcd") or style == "vfd_cyan":
        for y in range(2, height - 2, 2):
            draw.line([(2, y), (width - 3, y)], fill=tuple(min(255, c + 8) for c in bg))

    # optional ERROR / FAULT caption
    if height > 40 and rng.random() < 0.85:
        small = _font(max(8, height // 8))
        label = rng.choice(["ERROR", "FAULT", "CODE", "ERR"])
        bb = draw.textbbox((0, 0), label, font=small)
        draw.text(((width - (bb[2] - bb[0])) // 2, 3), label, font=small, fill=tuple(c // 2 + 20 for c in fg))

    font_size = max(14, min(height // 2, width // max(2, len(code))))
    font = _font(font_size)
    bb = draw.textbbox((0, 0), code, font=font)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    x = (width - tw) // 2 - bb[0]
    y = (height - th) // 2 - bb[1] + height // 16
    if style.startswith("led") or style == "vfd_cyan":
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            draw.text((x + dx, y + dy), code, font=font, fill=tuple(c // 4 for c in fg))
    draw.text((x, y), code, font=font, fill=fg)
    return lcd


def render_full_panel(
    code: str,
    machine: str = "washer",
    size: int = 256,
    style: str | None = None,
    seed: int | None = None,
    *,
    finish: str | None = None,
    scene: str | None = None,
    framing: str | None = None,
    include_scene: bool = True,
) -> Image.Image:
    """
    Render a claim-like image of a machine display.

    framing:
      - tight: mostly the LCD
      - panel: control panel with buttons
      - wide: machine face in a room (default when include_scene)
    """
    code = code.upper().strip()
    rng = random.Random(seed)
    theme = MACHINE_THEMES.get(machine.lower(), MACHINE_THEMES["generic"])
    style = style or rng.choice(theme["styles"])
    finish = finish or rng.choice(theme["finishes"])
    body = BODY_FINISHES.get(finish, BODY_FINISHES["graphite"])
    accent = rng.choice(theme["accents"])
    scene = scene or rng.choice(SCENE_BACKDROPS)
    framing = framing or rng.choice(["tight", "panel", "panel", "wide", "wide"])

    if not include_scene:
        framing = framing if framing != "wide" else "panel"

    # Base canvas = room or solid body color
    if include_scene and framing == "wide":
        img = _scene_background(size, scene, rng)
    elif finish in {"white", "off_white", "beige", "stainless", "silver"}:
        img = Image.new("RGB", (size, size), body)
    else:
        # still allow light room behind dark machines
        if include_scene and rng.random() < 0.7:
            img = _scene_background(size, scene, rng)
        else:
            img = Image.new("RGB", (size, size), body)

    draw = ImageDraw.Draw(img)

    # Appliance body rectangle placement by framing
    if framing == "tight":
        # almost full-frame LCD with thin bezel
        margin = size // 20
        bezel = tuple(max(0, c - 30) for c in body)
        draw.rounded_rectangle([margin, margin, size - margin, size - margin], radius=size // 24, fill=bezel)
        lcd_box = (margin + size // 16, margin + size // 16, size - margin - size // 16, size - margin - size // 16)
    elif framing == "panel":
        m = size // 18
        # panel plate
        draw.rounded_rectangle([m, m, size - m, size - m], radius=size // 20, fill=body)
        # accent brand strip
        strip_h = size // 9
        strip_color = accent if sum(body) > 200 else tuple(min(255, c + 40) for c in accent)
        draw.rectangle([m + 6, m + 8, size - m - 6, m + 8 + strip_h], fill=strip_color)
        title_color = (20, 20, 25) if sum(strip_color) > 400 else (250, 250, 250)
        tf = _font(max(10, size // 18))
        title = theme["label"]
        bb = draw.textbbox((0, 0), title, font=tf)
        draw.text(((size - (bb[2] - bb[0])) // 2, m + 10 + strip_h // 6), title, font=tf, fill=title_color)
        lcd_top = m + 12 + strip_h + size // 22
        lcd_bot = size - m - size // 8
        lcd_left = m + size // 10
        lcd_right = size - m - size // 10
        lcd_box = (lcd_left, lcd_top, lcd_right, lcd_bot)
        # buttons
        by = size - m - size // 11
        btn_w = size // 14
        btn_fill = (40, 40, 45) if sum(body) > 200 else (20, 20, 22)
        for i in range(4):
            bx = m + size // 7 + i * (btn_w + size // 14)
            draw.ellipse([bx, by, bx + btn_w, by + btn_w // 2], fill=btn_fill, outline=accent)
    else:  # wide — machine in room
        # floor shadow
        machine_top = int(size * 0.12)
        machine_bot = int(size * 0.92)
        machine_left = int(size * 0.18)
        machine_right = int(size * 0.82)
        draw.rounded_rectangle(
            [machine_left, machine_top, machine_right, machine_bot],
            radius=size // 30,
            fill=body,
        )
        # door line
        mid = (machine_top + machine_bot) // 2
        draw.line(
            [(machine_left + 8, mid), (machine_right - 8, mid)], fill=tuple(max(0, c - 25) for c in body), width=2
        )
        # control panel band near top
        panel_bot = machine_top + int((machine_bot - machine_top) * 0.28)
        draw.rectangle(
            [machine_left + 4, machine_top + 4, machine_right - 4, panel_bot], fill=tuple(max(0, c - 15) for c in body)
        )
        lcd_box = (
            machine_left + int((machine_right - machine_left) * 0.2),
            machine_top + int((panel_bot - machine_top) * 0.25),
            machine_right - int((machine_right - machine_left) * 0.2),
            panel_bot - int((panel_bot - machine_top) * 0.15),
        )
        # brand strip
        draw.rectangle(
            [machine_left + 10, machine_top + 6, machine_right - 10, machine_top + size // 18],
            fill=accent,
        )

    # LCD recess + module
    lx0, ly0, lx1, ly1 = (int(v) for v in lcd_box)
    recess = tuple(max(0, c - 50) for c in body) if sum(body) > 120 else (15, 15, 18)
    draw.rounded_rectangle([lx0 - 3, ly0 - 3, lx1 + 3, ly1 + 3], radius=4, fill=recess)
    lcd = render_lcd_module(code, style, max(8, lx1 - lx0), max(8, ly1 - ly0), rng)
    img.paste(lcd, (lx0, ly0))

    # lighting variation
    img = ImageEnhance.Brightness(img).enhance(rng.uniform(0.85, 1.2))
    img = ImageEnhance.Color(img).enhance(rng.uniform(0.75, 1.25))
    if rng.random() < 0.35:
        img = ImageEnhance.Contrast(img).enhance(rng.uniform(0.9, 1.3))
    return img


def render_training_variant(
    code: str,
    machine: str = "washer",
    size: int = 64,
    seed: int | None = None,
    phone_aug: bool = False,
) -> Image.Image:
    """One diverse training sample (domain-randomized)."""
    rng = random.Random(seed)
    img = render_full_panel(
        code,
        machine=machine,
        size=max(size, 128) if size < 128 else size,
        seed=seed,
        include_scene=True,
        framing=rng.choice(["tight", "panel", "panel", "wide"]),
    )
    if size != img.size[0]:
        img = img.resize((size, size), Image.BICUBIC)
    if phone_aug:
        img = phone_camera_augment(img, rng=random.Random((seed or 0) + 99))
    return img


def phone_camera_augment(img: Image.Image, rng: random.Random | None = None) -> Image.Image:
    """Phone claim-photo degradations; fill color matches scene (not pure black)."""
    rng = rng or random.Random()
    out = img.convert("RGB")
    # sample edge color for rotate fill so we don't invent black letterboxes
    arr0 = np.array(out)
    fill = tuple(int(x) for x in arr0[0, 0])
    fill2 = tuple(int(x) for x in arr0[-1, -1])
    fill_c = tuple((a + b) // 2 for a, b in zip(fill, fill2, strict=False))

    if rng.random() < 0.9:
        out = out.rotate(rng.uniform(-18, 18), resample=Image.BICUBIC, fillcolor=fill_c)
    if rng.random() < 0.75:
        w, h = out.size
        out = out.transform(
            out.size,
            Image.AFFINE,
            (
                1,
                rng.uniform(-0.12, 0.12),
                rng.uniform(-0.06, 0.06) * w,
                rng.uniform(-0.12, 0.12),
                1,
                rng.uniform(-0.06, 0.06) * h,
            ),
            resample=Image.BICUBIC,
            fillcolor=fill_c,
        )
    out = ImageEnhance.Brightness(out).enhance(rng.uniform(0.55, 1.35))
    out = ImageEnhance.Contrast(out).enhance(rng.uniform(0.7, 1.45))
    out = ImageEnhance.Color(out).enhance(rng.uniform(0.6, 1.35))
    if rng.random() < 0.55:
        out = out.filter(ImageFilter.GaussianBlur(radius=rng.uniform(0.3, 1.6)))
    if rng.random() < 0.55:
        arr = np.array(out).astype(np.float32)
        h, w, _ = arr.shape
        cy, cx = rng.uniform(0.2, 0.8) * h, rng.uniform(0.2, 0.8) * w
        yy, xx = np.mgrid[0:h, 0:w]
        sigma = rng.uniform(w * 0.08, w * 0.22)
        blob = np.exp(-((yy - cy) ** 2 + (xx - cx) ** 2) / (2 * sigma**2))
        arr = np.clip(arr + (blob * rng.uniform(25, 100))[..., None], 0, 255)
        out = Image.fromarray(arr.astype(np.uint8))
    if rng.random() < 0.75:
        arr = np.array(out).astype(np.float32)
        noise = np.random.normal(0, rng.uniform(3, 16), arr.shape)
        out = Image.fromarray(np.clip(arr + noise, 0, 255).astype(np.uint8))
    # occasional JPEG-like quality drop
    if rng.random() < 0.3:
        from io import BytesIO

        buf = BytesIO()
        out.save(buf, format="JPEG", quality=rng.randint(35, 75))
        buf.seek(0)
        out = Image.open(buf).convert("RGB")
    return out


def describe_data_provenance() -> dict[str, Any]:
    """Document for notebooks / clients: what models learn from."""
    return {
        "real_claim_photos": "none_in_repo",
        "training_source": "procedural_simulation",
        "simulates": [
            "room backdrops (laundry/kitchen/tile/wood/garage)",
            "appliance finishes (white/stainless/black/graphite)",
            "display types (green/blue/gray LCD, LED, OLED, VFD)",
            "framing (tight LCD, control panel, machine-in-room)",
            "phone camera (tilt, blur, glare, noise, jpeg)",
        ],
        "learning_implication": (
            "GAN/diffusion can only generate variations of this simulated distribution "
            "until real photos are added to the training manifest (source=real)."
        ),
        "how_to_add_real_photos": (
            "Place images on disk, append rows to manifest with source=real, "
            "code=, machine=, class_idx=; retrain cGAN/DDPM/OCR."
        ),
    }
