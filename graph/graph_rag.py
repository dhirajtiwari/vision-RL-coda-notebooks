"""
GraphRAG layer: query the Neo4j knowledge graph for diagnosis evidence.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from config.settings import settings
from graph.neo4j_client import get_driver
from graph.provenance import provenance_evidence_line


@dataclass
class DiagnosisResult:
    product_id: str
    product_name: str
    matched_symptoms: list[dict[str, Any]] = field(default_factory=list)
    ranked_failure_modes: list[dict[str, Any]] = field(default_factory=list)
    diagnostic_steps: list[dict[str, Any]] = field(default_factory=list)
    parts: list[dict[str, Any]] = field(default_factory=list)
    historical_resolutions: list[dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    should_escalate: bool = False
    escalation_reason: str = ""
    evidence: list[str] = field(default_factory=list)
    provenance_trail: list[dict[str, Any]] = field(default_factory=list)
    asset_id: str = ""
    model_number: str = ""
    sku_id: str = ""
    serial_number: str = ""
    matched_error_codes: list[dict[str, Any]] = field(default_factory=list)
    impacted_components: list[dict[str, Any]] = field(default_factory=list)
    predicted_parts: list[dict[str, Any]] = field(default_factory=list)
    claim_precedents: list[dict[str, Any]] = field(default_factory=list)
    diagnostic_tree: dict[str, Any] = field(default_factory=dict)


SYNONYMS = {
    "spin": {"spin", "spins", "spinning", "rotate", "rotation"},
    "water": {"water", "drain", "drainage", "flooded"},
    "drum": {"drum", "tub"},
    "noise": {"noise", "vibration", "banging", "grinding", "loud"},
    "cold": {"cold", "chill", "cool", "wet"},
    "arcing": {"arcing", "spark", "sparking", "sparks"},
    "heat": {"heat", "heating", "hot", "warm", "temperature"},
}


def _tokenize(text: str) -> set[str]:
    tokens = {t for t in re.findall(r"[a-z0-9]+", text.lower()) if len(t) > 2}
    expanded = set(tokens)
    for key, group in SYNONYMS.items():
        if tokens & group:
            expanded |= group
    return expanded


def _text_similarity(a: str, b: str) -> float:
    a_lower, b_lower = a.lower(), b.lower()
    if a_lower in b_lower or b_lower in a_lower:
        return 0.85
    a_tokens, b_tokens = _tokenize(a), _tokenize(b)
    if not a_tokens or not b_tokens:
        return 0.0
    overlap = a_tokens & b_tokens
    return len(overlap) / max(len(b_tokens), 1)


def _load_json_catalog() -> dict[str, Any]:
    with open(settings.data_file, encoding="utf-8") as f:
        return json.load(f)


def list_products() -> list[dict[str, Any]]:
    driver = get_driver()
    with driver.session() as session:
        result = session.run("""
            MATCH (p:Product)
            RETURN p.product_id AS product_id, p.name AS name,
                   p.category AS category, p.brand AS brand
            ORDER BY p.name
        """)
        return [dict(r) for r in result]


def detect_product(user_message: str) -> dict[str, Any] | None:
    message = user_message.lower()
    keywords = {
        "wm-001": ["washing", "washer", "laundry", "spin", "drum", "aquahome"],
        "dw-001": ["dishwasher", "dish", "dishes", "rinse", "cleanwave"],
        "mw-001": ["microwave", "convection", "magnetron", "arcing", "spark", "heatpro"],
        "oem-sam-wf45": ["samsung", "wf45", "wf45t6000", "4e", "5e", "ue"],
        "oem-lg-ldf5545": ["lg", "ldf5545", "ldf5545st"],
        "oem-whi-wtw5000": ["whirlpool", "wtw5000", "f9 e1", "f9e1"],
        "oem-bos-shpm88": ["bosch", "shpm88", "e24", "e01"],
        "oem-ge-jvm3160": ["ge", "jvm3160", "over-the-range", "otr microwave"],
        "oem-sam-rf28": ["samsung", "rf28", "rf28r7351", "refrigerator", "22e", "33e", "not cooling"],
        "oem-lg-dle3400": ["lg", "dle3400", "dryer", "d80", "d90", "d95", "vent"],
        "oem-whi-wfg505": ["whirlpool", "wfg505", "range", "oven", "f9e0", "f9 e0", "igniter"],
        "oem-sam-dw80": ["samsung", "dw80", "dw80b7070", "lc", "oc", "dishwasher"],
        "oem-lg-wm4000": ["lg", "wm4000", "wm4000hwa", "oe", "de"],
    }
    products = {p["product_id"]: p for p in list_products()}
    scores: dict[str, int] = {}
    for product_id, terms in keywords.items():
        scores[product_id] = sum(1 for t in terms if t in message)
    best_id = max(scores, key=scores.get)
    if scores[best_id] > 0:
        return products.get(best_id)
    return None


def match_symptoms(product_id: str, user_message: str) -> list[dict[str, Any]]:
    driver = get_driver()
    with driver.session() as session:
        symptoms = session.run("""
            MATCH (p:Product {product_id: $product_id})-[:HAS_SYMPTOM]->(s:Symptom)
            RETURN s.symptom_id AS symptom_id, s.description AS description,
                   s.severity AS severity,
                   s.source_system AS source_system,
                   s.source_record_id AS source_record_id,
                   s.source_document_uri AS source_document_uri,
                   s.approval_status AS approval_status
        """, product_id=product_id)
        symptom_list = [dict(r) for r in symptoms]

    matched = []
    for symptom in symptom_list:
        score = _text_similarity(user_message, symptom["description"])
        if score >= 0.15:
            matched.append({**symptom, "match_score": round(score, 2)})

    if not matched and symptom_list:
        matched = [{**s, "match_score": 0.1} for s in symptom_list[:2]]

    matched.sort(key=lambda x: x["match_score"], reverse=True)
    return matched[:4]


def list_failure_modes(product_id: str) -> list[dict[str, Any]]:
    driver = get_driver()
    with driver.session() as session:
        result = session.run("""
            MATCH (p:Product {product_id: $product_id})-[:CAN_HAVE]->(fm:FailureMode)
            RETURN fm.failure_mode_id AS failure_mode_id,
                   fm.name AS name,
                   fm.description AS description,
                   fm.estimated_repair_time_minutes AS repair_minutes,
                   fm.safety_notes AS safety_notes
            ORDER BY fm.name
        """, product_id=product_id)
        return [dict(r) for r in result]


def rank_failure_modes(product_id: str, symptom_ids: list[str]) -> list[dict[str, Any]]:
    if not symptom_ids:
        failures = list_failure_modes(product_id)
        return [
            {**fm, "indications": [], "total_confidence": 0, "link_count": 0, "aggregate_confidence": 0.0}
            for fm in failures
        ]

    driver = get_driver()
    with driver.session() as session:
        result = session.run("""
            MATCH (p:Product {product_id: $product_id})-[:CAN_HAVE]->(fm:FailureMode)
            OPTIONAL MATCH (s:Symptom)-[ind:INDICATES]->(fm)
            WHERE s.symptom_id IN $symptom_ids
            WITH fm, collect(DISTINCT {symptom_id: s.symptom_id, confidence: ind.confidence}) AS indications,
                 sum(CASE WHEN ind.confidence IS NULL THEN 0 ELSE ind.confidence END) AS total_confidence,
                 count(ind) AS link_count
            RETURN fm.failure_mode_id AS failure_mode_id,
                   fm.name AS name,
                   fm.description AS description,
                   fm.estimated_repair_time_minutes AS repair_minutes,
                   fm.safety_notes AS safety_notes,
                   fm.source_system AS source_system,
                   fm.source_record_id AS source_record_id,
                   fm.source_document_uri AS source_document_uri,
                   indications,
                   total_confidence,
                   link_count
            ORDER BY total_confidence DESC, link_count DESC
        """, product_id=product_id, symptom_ids=symptom_ids)
        ranked = []
        for record in result:
            row = dict(record)
            row["aggregate_confidence"] = round(
                row["total_confidence"] / max(len(symptom_ids), 1), 2
            )
            ranked.append(row)
        return ranked


def resolve_asset_context(asset_id: str) -> dict[str, Any] | None:
    driver = get_driver()
    with driver.session() as session:
        row = session.run(
            """
            MATCH (a:Asset {asset_id: $asset_id})-[:INSTANCE_OF]->(p:Product)
            OPTIONAL MATCH (a)-[:BOUND_TO_SKU]->(sku:SKU)
            OPTIONAL MATCH (p)-[:HAS_MODEL]->(m:Model)
            RETURN a.asset_id AS asset_id, a.serial_number AS serial_number,
                   a.model_number AS model_number, a.customer_id AS customer_id,
                   p.product_id AS product_id, p.name AS product_name,
                   sku.sku_id AS sku_id, m.model_number AS graph_model_number
            """,
            asset_id=asset_id,
        ).single()
        return dict(row) if row else None


def match_error_codes(product_id: str, user_message: str) -> list[dict[str, Any]]:
    driver = get_driver()
    message = user_message.upper()
    with driver.session() as session:
        codes = session.run(
            """
            MATCH (p:Product {product_id: $product_id})-[:HAS_ERROR_CODE]->(ec:ErrorCode)
            RETURN ec.error_code_id AS error_code_id, ec.code AS code, ec.description AS description
            """,
            product_id=product_id,
        )
        matched = []
        for row in codes:
            code = row["code"]
            if code.upper() in message or f"ERROR CODE {code.upper()}" in message:
                matched.append(dict(row))
        return matched


def rank_failure_modes_with_error_codes(
    product_id: str,
    symptom_ids: list[str],
    error_code_ids: list[str],
) -> list[dict[str, Any]]:
    ranked = rank_failure_modes(product_id, symptom_ids)
    if not error_code_ids:
        return ranked

    driver = get_driver()
    with driver.session() as session:
        boosts = session.run(
            """
            MATCH (ec:ErrorCode)-[r:INDICATES]->(fm:FailureMode)
            WHERE ec.error_code_id IN $error_code_ids
            RETURN fm.failure_mode_id AS failure_mode_id, sum(r.confidence) AS error_boost
            """,
            error_code_ids=error_code_ids,
        )
        boost_map = {row["failure_mode_id"]: row["error_boost"] for row in boosts}

    for row in ranked:
        fid = row["failure_mode_id"]
        if fid in boost_map:
            row["error_code_boost"] = round(boost_map[fid], 2)
            row["total_confidence"] = (row.get("total_confidence") or 0) + boost_map[fid]
            row["aggregate_confidence"] = round(
                row["total_confidence"] / max(len(symptom_ids) + len(error_code_ids), 1), 2
            )

    ranked.sort(key=lambda x: (x.get("total_confidence", 0), x.get("link_count", 0)), reverse=True)
    return ranked


def get_diagnostic_steps_for_failure_mode(
    product_id: str,
    failure_mode_id: str,
) -> list[dict[str, Any]]:
    driver = get_driver()
    with driver.session() as session:
        result = session.run(
            """
            MATCH (p:Product {product_id: $product_id})-[:HAS_DIAGNOSTIC_STEP]->(ds:DiagnosticStep)
                  -[:CONFIRMS]->(fm:FailureMode {failure_mode_id: $failure_mode_id})
            RETURN ds.step_id AS step_id, ds.description AS description,
                   ds.order AS step_order, ds.expected_outcome AS expected_outcome,
                   ds.source_system AS source_system, ds.source_document_uri AS source_document_uri
            ORDER BY ds.order
            """,
            product_id=product_id,
            failure_mode_id=failure_mode_id,
        )
        steps = [dict(r) for r in result]
        if steps:
            return steps
    return get_diagnostic_steps(product_id)


def get_impacted_components(product_id: str, failure_mode_id: str) -> list[dict[str, Any]]:
    driver = get_driver()
    with driver.session() as session:
        result = session.run(
            """
            MATCH (p:Product {product_id: $product_id})-[:CAN_HAVE]->(fm:FailureMode {failure_mode_id: $fm_id})
                  -[r:IMPACTS_COMPONENT]->(c:Component)
            RETURN c.component_id AS component_id, c.name AS name, c.subsystem AS subsystem,
                   r.impact_severity AS impact_severity
            ORDER BY c.name
            """,
            product_id=product_id,
            fm_id=failure_mode_id,
        )
        return [dict(r) for r in result]


def get_claim_precedents(failure_mode_id: str, asset_id: str | None = None) -> list[dict[str, Any]]:
    driver = get_driver()
    query = """
        MATCH (cl:Claim)-[:CONFIRMED]->(fm:FailureMode {failure_mode_id: $fm_id})
        OPTIONAL MATCH (cl)-[:FOR_ASSET]->(a:Asset)
        OPTIONAL MATCH (cl)-[:USED_PART]->(pt:Part)
        RETURN cl.claim_id AS claim_id, cl.resolution_summary AS resolution_summary,
               cl.closed_date AS closed_date, a.asset_id AS asset_id,
               pt.part_id AS used_part_id, pt.name AS used_part_name
        ORDER BY cl.closed_date DESC LIMIT 5
    """
    with driver.session() as session:
        rows = [dict(r) for r in session.run(query, fm_id=failure_mode_id)]
    if asset_id:
        asset_matches = [r for r in rows if r.get("asset_id") == asset_id]
        if asset_matches:
            return asset_matches
    return rows[:3]


def get_diagnostic_steps(product_id: str) -> list[dict[str, Any]]:
    driver = get_driver()
    with driver.session() as session:
        result = session.run("""
            MATCH (p:Product {product_id: $product_id})-[:HAS_DIAGNOSTIC_STEP]->(ds:DiagnosticStep)
            RETURN ds.step_id AS step_id, ds.description AS description,
                   ds.order AS step_order, ds.expected_outcome AS expected_outcome,
                   ds.source_system AS source_system,
                   ds.source_document_uri AS source_document_uri
            ORDER BY ds.order
        """, product_id=product_id)
        return [dict(r) for r in result]


def get_historical_resolutions(product_id: str, failure_mode_id: str | None = None) -> list[dict[str, Any]]:
    driver = get_driver()
    query = """
        MATCH (r:HistoricalResolution)-[:FOR_PRODUCT]->(p:Product {product_id: $product_id})
        OPTIONAL MATCH (r)-[:CONFIRMED]->(fm:FailureMode)
    """
    if failure_mode_id:
        query += " WHERE fm.failure_mode_id = $failure_mode_id"
    query += """
        RETURN r.resolution_id AS resolution_id, r.description AS description,
               r.resolution_date AS resolution_date, r.technician_notes AS technician_notes,
               r.source_system AS source_system, r.source_record_id AS source_record_id,
               fm.name AS failure_mode_name
        ORDER BY r.resolution_date DESC
    """
    params: dict[str, Any] = {"product_id": product_id}
    if failure_mode_id:
        params["failure_mode_id"] = failure_mode_id

    with driver.session() as session:
        result = session.run(query, **params)
        return [dict(r) for r in result]


def get_parts_for_product(
    product_id: str,
    failure_mode_id: str | None = None,
) -> list[dict[str, Any]]:
    driver = get_driver()
    query = """
        MATCH (p:Product {product_id: $product_id})-[:CAN_HAVE]->(fm:FailureMode)
    """
    if failure_mode_id:
        query += " WHERE fm.failure_mode_id = $failure_mode_id"
    query += """
        MATCH (fm)-[:REQUIRES_PART]->(pt:Part)
        RETURN pt.part_id AS part_id, pt.name AS name,
               pt.part_number AS part_number, pt.estimated_cost_usd AS estimated_cost_usd,
               fm.failure_mode_id AS failure_mode_id, fm.name AS failure_mode_name
        ORDER BY pt.name
    """
    params: dict[str, Any] = {"product_id": product_id}
    if failure_mode_id:
        params["failure_mode_id"] = failure_mode_id

    with driver.session() as session:
        result = session.run(query, **params)
        parts = [dict(r) for r in result]

    if parts:
        return parts

    catalog = _load_json_catalog()
    for item in catalog["products"]:
        if item["product"]["product_id"] == product_id:
            return item.get("parts", [])
    return []


def diagnose(
    user_message: str,
    product_id: str | None = None,
    asset_id: str | None = None,
) -> DiagnosisResult:
    asset_ctx: dict[str, Any] | None = None
    if asset_id:
        asset_ctx = resolve_asset_context(asset_id)
        if asset_ctx:
            product_id = asset_ctx.get("product_id") or product_id

    product = None
    if product_id:
        products = {p["product_id"]: p for p in list_products()}
        product = products.get(product_id)
    if not product:
        product = detect_product(user_message)

    if not product:
        return DiagnosisResult(
            product_id="",
            product_name="Unknown",
            should_escalate=True,
            escalation_reason="Could not identify appliance type from message.",
            evidence=["No product keyword match"],
        )

    pid = product["product_id"]
    sku_id = asset_ctx.get("sku_id", "") if asset_ctx else ""
    matched_error_codes = match_error_codes(pid, user_message)
    error_code_ids = [e["error_code_id"] for e in matched_error_codes]

    matched_symptoms = match_symptoms(pid, user_message)
    symptom_ids = [s["symptom_id"] for s in matched_symptoms]
    ranked = rank_failure_modes_with_error_codes(pid, symptom_ids, error_code_ids)

    top = ranked[0] if ranked else None
    confidence = top["aggregate_confidence"] if top else 0.0

    critical = any(s.get("severity") == "critical" for s in matched_symptoms)
    should_escalate = critical or confidence < settings.escalation_confidence_threshold
    escalation_reason = ""
    if critical:
        escalation_reason = "Critical severity symptom detected — human review required."
    elif confidence < settings.escalation_confidence_threshold:
        escalation_reason = f"Confidence ({confidence:.0%}) below threshold — escalating to human agent."

    top_fm_id = top["failure_mode_id"] if top else None
    evidence = []
    if asset_ctx:
        evidence.append(
            f"Asset {asset_ctx['asset_id']}: {asset_ctx.get('model_number', 'N/A')} "
            f"(SKU {sku_id or 'unknown'}, serial {asset_ctx.get('serial_number', '')})"
        )
    if top:
        evidence.append(f"Top failure mode: {top['name']} (confidence {confidence:.0%})")
    for ec in matched_error_codes:
        evidence.append(f"Error code match: {ec['code']} — {ec['description']}")
    for s in matched_symptoms[:3]:
        evidence.append(f"Symptom match: {s['description']} [{s.get('severity', 'unknown')}]")

    from graph.diagnostic_engine import get_diagnostic_tree, resolve_dynamic_steps

    steps = resolve_dynamic_steps(pid, top_fm_id) if top_fm_id else get_diagnostic_steps(pid)
    diagnostic_tree = get_diagnostic_tree(pid)
    resolutions = get_historical_resolutions(pid, top_fm_id)
    impacted_components = get_impacted_components(pid, top_fm_id) if top_fm_id else []
    claim_precedents = get_claim_precedents(top_fm_id, asset_id) if top_fm_id else []

    from graph.parts_predictor import predict_parts

    predicted_parts = predict_parts(pid, top_fm_id, sku_id=sku_id or None) if top_fm_id else []
    parts = predicted_parts or get_parts_for_product(pid, top_fm_id)

    provenance_trail: list[dict[str, Any]] = []
    if settings.enable_provenance:
        for s in matched_symptoms[:3]:
            provenance_trail.append(
                provenance_evidence_line("Symptom", s.get("symptom_id", ""), s)
            )
        if top:
            provenance_trail.append(
                provenance_evidence_line("FailureMode", top.get("failure_mode_id", ""), top)
            )
        for step in steps[:2]:
            provenance_trail.append(
                provenance_evidence_line("DiagnosticStep", step.get("step_id", ""), step)
            )
        for part in predicted_parts[:2]:
            provenance_trail.append(
                provenance_evidence_line("Part", part.get("part_id", ""), part)
            )
        for res in resolutions[:1]:
            provenance_trail.append(
                provenance_evidence_line("HistoricalResolution", res.get("resolution_id", ""), res)
            )

    return DiagnosisResult(
        product_id=pid,
        product_name=product["name"],
        matched_symptoms=matched_symptoms,
        ranked_failure_modes=ranked[:3],
        diagnostic_steps=steps,
        parts=parts,
        historical_resolutions=resolutions,
        confidence=confidence,
        should_escalate=should_escalate,
        escalation_reason=escalation_reason,
        evidence=evidence,
        provenance_trail=provenance_trail,
        asset_id=asset_ctx.get("asset_id", "") if asset_ctx else "",
        model_number=asset_ctx.get("model_number", "") if asset_ctx else "",
        sku_id=sku_id,
        serial_number=asset_ctx.get("serial_number", "") if asset_ctx else "",
        matched_error_codes=matched_error_codes,
        impacted_components=impacted_components,
        predicted_parts=predicted_parts,
        claim_precedents=claim_precedents,
        diagnostic_tree=diagnostic_tree,
    )


def format_diagnosis_response(result: DiagnosisResult) -> str:
    if not result.product_id:
        return (
            "I couldn't identify which appliance you're asking about. "
            "Please mention washing machine, dishwasher, or microwave."
        )

    lines = [f"**Product:** {result.product_name}"]
    if result.model_number or result.asset_id:
        lines.append(
            f"**Asset:** {result.asset_id or 'N/A'} · Model {result.model_number or 'N/A'} "
            f"· SKU {result.sku_id or 'N/A'}"
        )
    lines.extend(["", "**Matched Symptoms:**"])
    for s in result.matched_symptoms[:3]:
        lines.append(f"- {s['description']} (severity: {s['severity']})")

    if result.matched_error_codes:
        lines.extend(["", "**Matched Error Codes:**"])
        for ec in result.matched_error_codes:
            lines.append(f"- {ec['code']}: {ec['description']}")

    if result.ranked_failure_modes:
        top = result.ranked_failure_modes[0]
        lines.extend([
            "",
            f"**Most Likely Diagnosis (Failure Mode):** {top['name']}",
            f"- {top['description']}",
            f"- Estimated repair time: {top['repair_minutes']} minutes",
            f"- Safety: {top['safety_notes']}",
            f"- Confidence: {result.confidence:.0%}",
        ])

    if result.impacted_components:
        lines.extend(["", "**Impacted Components (BOM):**"])
        for comp in result.impacted_components:
            lines.append(f"- {comp['name']} ({comp['subsystem']}) — {comp.get('impact_severity', 'impact')}")

    if result.diagnostic_steps:
        lines.extend(["", "**Targeted Troubleshooting Steps:**"])
        for step in result.diagnostic_steps[:4]:
            lines.append(f"{step['step_order']}. {step['description']}")

    parts = result.predicted_parts or result.parts
    if parts:
        lines.extend(["", "**Predicted Parts Required:**"])
        for part in parts[:4]:
            score = part.get("prediction_score")
            score_txt = f" ({score:.0%} confidence)" if score else ""
            qty = part.get("quantity", 1)
            lines.append(
                f"- {part['name']} · `{part.get('part_number', '')}` · "
                f"qty {qty} · ${part.get('estimated_cost_usd', 0):.2f}{score_txt}"
            )
            if part.get("impacted_components"):
                lines.append(f"  - Impacts: {', '.join(part['impacted_components'])}")
            if part.get("claim_precedents"):
                lines.append(f"  - Prior claim: {', '.join(part['claim_precedents'])}")

    if result.claim_precedents:
        lines.extend(["", "**Warranty Claim Precedents:**"])
        for cl in result.claim_precedents[:2]:
            lines.append(f"- {cl.get('claim_id')}: {cl.get('resolution_summary', '')}")

    if result.historical_resolutions:
        lines.extend(["", "**Similar Past Resolutions:**"])
        for res in result.historical_resolutions[:2]:
            lines.append(f"- {res['description']} ({res['resolution_date']})")

    if result.should_escalate:
        lines.extend([
            "",
            f"**Escalation:** {result.escalation_reason}",
            "A human agent will review this case.",
        ])
    else:
        lines.extend(["", "**Status:** Resolved at automated tier (no escalation needed)."])

    lines.extend(["", "**Graph Evidence:**"] + [f"- {e}" for e in result.evidence])
    if result.provenance_trail:
        lines.extend(["", "**Source Traceability:**"])
        for pt in result.provenance_trail[:5]:
            src = pt.get("source_system", "Unknown")
            doc = pt.get("source_document_uri") or pt.get("source_record_id", "")
            lines.append(f"- {pt.get('entity_type')}: {src} — {doc}")
    return "\n".join(lines)