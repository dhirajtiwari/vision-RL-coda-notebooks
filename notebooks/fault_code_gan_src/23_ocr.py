# Closed-set catalog codes, longest first to avoid partials (e.g. F9E1 before E1)
_CATALOG_SORTED = sorted((row["code"].upper() for row in FAULT_CATALOG), key=len, reverse=True)
_CODE_RE = re.compile(r"\b([A-Z]{0,2}\d{1,2}[A-Z]{0,2}\d{0,2})\b")


def extract_fault_code_from_text(text: str) -> str | None:
    """Map free text / OCR string -> catalog code if present."""
    if not text:
        return None
    up = text.upper()
    for code in _CATALOG_SORTED:
        if re.search(rf"(?<![A-Z0-9]){re.escape(code)}(?![A-Z0-9])", up):
            return code
    m = _CODE_RE.search(up.replace("ERROR", " "))
    if m:
        cand = m.group(1)
        if cand in CODE_TO_IDX:
            return cand
    return None


def simple_pixel_template_ocr(
    img: Image.Image, templates: dict[str, Image.Image] | None = None
) -> str | None:
    """Ultra-light closed-set recognizer via NCC vs seed templates."""
    if templates is None:
        templates = {
            row["code"]: render_lcd_panel(row["code"], style="lcd_dark", size=IMG_SIZE)
            for row in FAULT_CATALOG
        }
    g = np.asarray(img.convert("L").resize((IMG_SIZE, IMG_SIZE)), dtype=np.float32)
    g = (g - g.mean()) / (g.std() + 1e-6)
    best_code, best_score = None, -1e9
    for code, tmpl in templates.items():
        t = np.asarray(tmpl.convert("L").resize((IMG_SIZE, IMG_SIZE)), dtype=np.float32)
        t = (t - t.mean()) / (t.std() + 1e-6)
        score = float((g * t).mean())
        if score > best_score:
            best_score, best_code = score, code
    return best_code


def tesseract_ocr(img: Image.Image) -> str | None:
    try:
        import pytesseract
        from pytesseract import TesseractNotFoundError
    except ImportError:
        return None
    try:
        big = img.resize((img.width * 4, img.height * 4), Image.BICUBIC)
        big = ImageOps.autocontrast(big.convert("L"))
        txt = pytesseract.image_to_string(
            big,
            config="--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
        )
        return extract_fault_code_from_text(txt)
    except (TesseractNotFoundError, OSError):
        # Package installed but binary missing, or OCR runtime failure
        return None


def extract_code_from_image(img: Image.Image) -> tuple[str | None, str]:
    """Returns (code, method)."""
    t = tesseract_ocr(img)
    if t:
        return t, "tesseract"
    c = simple_pixel_template_ocr(img)
    return c, "template_ncc"


def evaluate_extraction(meta: list[dict], max_n: int | None = 200) -> dict:
    rows = meta if max_n is None else meta[:max_n]
    correct = 0
    details = []
    for row in rows:
        img = Image.open(row["path"]).convert("RGB")
        pred, method = extract_code_from_image(img)
        ok = pred == row["code"]
        correct += int(ok)
        details.append(
            {
                "truth": row["code"],
                "pred": pred,
                "ok": ok,
                "method": method,
                "path": row["path"],
            }
        )
    acc = correct / max(len(rows), 1)
    report = {
        "n": len(rows),
        "correct": correct,
        "accuracy": acc,
        "method_mix": list({d["method"] for d in details}),
    }
    print(f"Extraction accuracy: {acc:.1%} ({correct}/{len(rows)}) methods={report['method_mix']}")
    misses = [d for d in details if not d["ok"]][:8]
    if misses:
        print("Sample misses:")
        for m in misses:
            print(f"  truth={m['truth']} pred={m['pred']} via {m['method']}")
    with open(ART / "ocr_eval_report.json", "w") as f:
        json.dump({"summary": report, "details": details}, f, indent=2)
    return report


clean_holdout = [m for m in seed_meta if m["style"] == "lcd_dark"][: N_CLASSES * 2]
print("--- Clean seeds ---")
evaluate_extraction(clean_holdout)
print("--- Synthetic claim-style ---")
evaluate_extraction(synth_meta)
