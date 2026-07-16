# Mini ABox mirror of catalog relationships (illustrative; production = Neo4j)
LOCAL_GRAPH = {
    "UE": {"failure_modes": [("unbalanced_load", 0.75)], "steps": ["Redistribute load", "Run calibration spin"]},
    "4E": {"failure_modes": [("inlet_valve_fault", 0.68)], "steps": ["Check water supply taps", "Inspect inlet screens"]},
    "5E": {
        "failure_modes": [("drain_pump_block", 0.92)],
        "steps": ["Clean drain filter", "Inspect drain hose"],
        "parts": ["drain_pump", "drain_filter"],
    },
    "OE": {"failure_modes": [("drain_timeout", 0.90)], "steps": ["Verify standpipe height", "Check pump"]},
    "IE": {"failure_modes": [("fill_insufficient", 0.93)], "steps": ["Confirm inlet pressure", "Test pressure sensor"]},
    "HE": {"failure_modes": [("heater_fault", 0.92)], "steps": ["Measure heater resistance", "Check NTC sensor"]},
    "AE": {"failure_modes": [("leak_detected", 0.55)], "steps": ["Inspect base tray", "Check hoses"]},
    "E24": {"failure_modes": [("drain_issue", 0.95)], "steps": ["Clear filter", "Test drain pump"]},
    "E01": {"failure_modes": [("pump_failure", 0.96)], "steps": ["Ohm-test pump", "Replace if open circuit"]},
    "F9E1": {"failure_modes": [("drain_pump_fault", 0.96)], "steps": ["Replace drain pump", "Verify harness"]},
    "F9E0": {"failure_modes": [("drain_system_fault", 0.90)], "steps": ["Inspect drain path"]},
    "22E": {"failure_modes": [("evap_fan_error", 0.96)], "steps": ["Test evaporator fan"]},
    "33E": {"failure_modes": [("ice_fan_error", 0.95)], "steps": ["Test ice-maker fan"]},
    "39E": {"failure_modes": [("ice_function_error", 0.90)], "steps": ["Run ice-maker diagnostics"]},
    "LC": {"failure_modes": [("control_lock", 0.99)], "steps": ["Hold temp buttons 3s to unlock"]},
    "OC": {"failure_modes": [("overload", 0.85)], "steps": ["Reduce load", "Inspect motor current"]},
    "DE": {"failure_modes": [("door_error", 0.90)], "steps": ["Check door switch / latch"]},
}


def cypher_for_extracted_code(code: str, product_id: str = "wm-001") -> dict:
    """Return the Cypher statements our GraphRAG layer effectively needs."""
    q_match = """
MATCH (p:Product {product_id: $product_id})-[:HAS_ERROR_CODE]->(ec:ErrorCode)
WHERE toUpper(ec.code) = toUpper($code)
RETURN ec.error_code_id AS error_code_id,
       ec.code AS code,
       ec.description AS description
""".strip()
    q_fm = """
MATCH (p:Product {product_id: $product_id})-[:HAS_ERROR_CODE]->(ec:ErrorCode)
WHERE toUpper(ec.code) = toUpper($code)
MATCH (ec)-[r:INDICATES]->(fm:FailureMode)
RETURN fm.failure_mode_id AS failure_mode_id,
       fm.name AS name,
       r.confidence AS confidence
ORDER BY r.confidence DESC
""".strip()
    q_res = """
MATCH (p:Product {product_id: $product_id})-[:HAS_ERROR_CODE]->(ec:ErrorCode)
WHERE toUpper(ec.code) = toUpper($code)
MATCH (ec)-[:INDICATES]->(fm:FailureMode)
OPTIONAL MATCH (ds:DiagnosticStep)-[c:CONFIRMS]->(fm)
OPTIONAL MATCH (fm)-[:REQUIRES_PART]->(part:Part)
OPTIONAL MATCH (hr:HistoricalResolution)-[:RESOLVED]->(fm)
RETURN ec, fm,
       collect(DISTINCT ds) AS confirm_steps,
       collect(DISTINCT part) AS parts,
       collect(DISTINCT hr) AS historical
""".strip()
    return {
        "match_code_on_product": q_match,
        "failure_modes_for_code": q_fm,
        "resolution_path": q_res,
        "params": {"product_id": product_id, "code": code},
    }


def diagnose_from_image(path, product_id: str = "wm-001") -> dict:
    img = Image.open(path).convert("RGB")
    code, method = extract_code_from_image(img)
    result = {
        "image": str(path),
        "extracted_code": code,
        "ocr_method": method,
        "product_id": product_id,
        "graph_hit": None,
        "cypher": None,
        "user_message_for_api": None,
    }
    if not code:
        result["error"] = "No fault code extracted — escalate or request retake photo"
        return result

    # Message format that match_error_codes() in graph_rag.py can consume
    result["user_message_for_api"] = (
        f"Customer uploaded display photo. Error code {code} shown on machine."
    )
    result["cypher"] = cypher_for_extracted_code(code, product_id=product_id)
    local = LOCAL_GRAPH.get(code, {})
    result["graph_hit"] = {
        "code": code,
        "description": next((r["description"] for r in FAULT_CATALOG if r["code"] == code), ""),
        "failure_modes": local.get("failure_modes", []),
        "diagnostic_steps": local.get("steps", []),
        "parts": local.get("parts", []),
        "note": "Local mirror for offline demo; production uses Neo4j INDICATES/CONFIRMS edges",
    }
    return result


demo_paths = [
    next(r["path"] for r in seed_meta if r["code"] == c and r["style"] == "lcd_dark")
    for c in ("5E", "UE", "E24", "F9E1")
]

for p in demo_paths:
    diag = diagnose_from_image(p, product_id="wm-001")
    print("=" * 72)
    print("IMAGE:", Path(diag["image"]).name)
    print("EXTRACTED:", diag["extracted_code"], f"({diag['ocr_method']})")
    print("API MESSAGE:", diag.get("user_message_for_api"))
    if diag.get("graph_hit"):
        print("FM:", diag["graph_hit"]["failure_modes"])
        print("STEPS:", diag["graph_hit"]["diagnostic_steps"])
    if diag.get("cypher"):
        print("--- Cypher: failure_modes_for_code ---")
        print(diag["cypher"]["failure_modes_for_code"])
        print("params:", diag["cypher"]["params"])
