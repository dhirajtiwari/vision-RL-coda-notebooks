## Part 7 — Extraction / OCR evaluation harness

Production systems typically use:

- commercial OCR (Azure Read, AWS Textract),
- `easyocr` / PaddleOCR / Tesseract,
- or a small fine-tuned CRNN / TrOCR on domain crops.

Here we implement a **domain-aware extractor** that:

1. prefers matches against the known catalog (closed-set codes),
2. falls back to alphanumeric regex,
3. scores accuracy on the labelled synthetic corpus (proxy metric until real photos exist).

> When real claim photos arrive: freeze a hold-out, re-run the same harness, and gate model promotion on real-image accuracy — never only synthetic (LLMOps / study module 20 guidance in this repo).
