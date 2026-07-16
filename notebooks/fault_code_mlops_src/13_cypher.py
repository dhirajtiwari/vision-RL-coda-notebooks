# End-to-end offline: image -> OCR -> API payload -> Cypher
# Prefer test split; fall back so this never raises StopIteration.
candidates = [r for r in rows if r["code"] == "5E" and r.get("split") == "test"]
if not candidates:
    candidates = [r for r in rows if r["code"] == "5E" and r.get("split") == "val"]
if not candidates:
    candidates = [r for r in rows if r["code"] == "5E"]
if not candidates:
    candidates = list(rows)
demo = candidates[0]
print("Using image:", demo["path"], "split=", demo.get("split"), "code=", demo.get("code"))

ocr = reader.predict(demo["path"], min_confidence=0.3)
payload = diagnose_payload_from_ocr(ocr, product_id="wm-001")

print("OCR:", {k: ocr[k] for k in ("code", "confidence", "accepted", "escalate")})
print("user_message:", payload.get("user_message"))
if payload.get("cypher"):
    print("\n--- Cypher: failure_modes_for_code ---")
    print(payload["cypher"]["failure_modes_for_code"])
    print("params:", payload["cypher"]["params"])
    print("\nAvailable Cypher keys:", list(cypher_for_extracted_code("5E").keys()))
else:
    print("No Cypher (OCR did not accept a code) — check confidence / training.")

api_contract = {
    "endpoint": "POST /claims/{id}/attachments  OR  POST /diagnose multipart",
    "request": {"product_id": "wm-001", "image": "<bytes>", "asset_id": "optional"},
    "response_fields": [
        "extracted_code",
        "confidence",
        "model_version",
        "ranked_failure_modes",
        "diagnostic_steps",
        "should_escalate",
    ],
    "graph_hooks": [
        "graph.graph_rag.match_error_codes",
        "graph.graph_rag.rank_failure_modes_with_error_codes",
    ],
}
print("\nAPI contract sketch:")
print(json.dumps(api_contract, indent=2))
(ART / "api_contract_sketch.json").write_text(json.dumps(api_contract, indent=2))
