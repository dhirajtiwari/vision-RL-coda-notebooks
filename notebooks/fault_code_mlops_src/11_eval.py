from ml.fault_code_vision.eval_vision import evaluate_checkpoint

# Prefer test; eval_vision falls back to val/train if needed
report = evaluate_checkpoint(ckpt_path, manifest_path, split="test")
summary = {k: report[k] for k in ("n", "correct", "accuracy", "checkpoint")}
print(json.dumps(summary, indent=2))

floor = 0.80  # vision_smoke (short notebook trains may be below floor — not a crash)
status = "PASS" if report["accuracy"] >= floor else "BELOW_FLOOR (train longer or more data)"
print(f"{status}: accuracy {report['accuracy']:.3f} vs floor {floor:.3f}")

report_path = ART / "ocr_eval_report.json"
report_path.write_text(json.dumps(report, indent=2))
print("wrote", report_path)

# Spot-check predictions
reader = FaultCodeReader(ckpt_path)
test_rows = [r for r in rows if r.get("split") == "test"][:6]
if not test_rows:
    test_rows = [r for r in rows if r.get("split") == "val"][:6]
if not test_rows:
    test_rows = rows[:6]

n_show = max(1, len(test_rows))
fig, axes = plt.subplots(1, n_show, figsize=(2.2 * n_show, 2.2))
if n_show == 1:
    axes = [axes]
for ax, row in zip(axes, test_rows):
    img = Image.open(row["path"])
    pred = reader.predict(img)
    ax.imshow(img)
    ok = "OK" if pred["code"] == row["code"] else "MISS"
    ax.set_title(f"{row['code']}→{pred['code']}\n{pred['confidence']:.2f} {ok}", fontsize=8)
    ax.axis("off")
plt.suptitle("OCR reader predictions")
plt.tight_layout()
plt.savefig(ART / "preview_ocr_preds.png", dpi=120)
plt.show()
