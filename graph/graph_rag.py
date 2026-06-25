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
        "wm-001": ["washing", "washer", "laundry", "spin", "drum"],
        "dw-001": ["dishwasher", "dish", "dishes", "rinse"],
        "mw-001": ["microwave", "convection", "magnetron", "arcing", "spark"],
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


def get_parts_for_product(product_id: str) -> list[dict[str, Any]]:
    catalog = _load_json_catalog()
    for item in catalog["products"]:
        if item["product"]["product_id"] == product_id:
            return item.get("parts", [])
    return []


def diagnose(user_message: str, product_id: str | None = None) -> DiagnosisResult:
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
    matched_symptoms = match_symptoms(pid, user_message)
    symptom_ids = [s["symptom_id"] for s in matched_symptoms]
    ranked = rank_failure_modes(pid, symptom_ids)

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
    if top:
        evidence.append(f"Top failure mode: {top['name']} (confidence {confidence:.0%})")
    for s in matched_symptoms[:3]:
        evidence.append(f"Symptom match: {s['description']} [{s.get('severity', 'unknown')}]")

    steps = get_diagnostic_steps(pid)
    resolutions = get_historical_resolutions(pid, top_fm_id)
    parts = get_parts_for_product(pid)

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
    )


def format_diagnosis_response(result: DiagnosisResult) -> str:
    if not result.product_id:
        return (
            "I couldn't identify which appliance you're asking about. "
            "Please mention washing machine, dishwasher, or microwave."
        )

    lines = [
        f"**Product:** {result.product_name}",
        "",
        "**Matched Symptoms:**",
    ]
    for s in result.matched_symptoms[:3]:
        lines.append(f"- {s['description']} (severity: {s['severity']})")

    if result.ranked_failure_modes:
        top = result.ranked_failure_modes[0]
        lines.extend([
            "",
            f"**Most Likely Failure Mode:** {top['name']}",
            f"- {top['description']}",
            f"- Estimated repair time: {top['repair_minutes']} minutes",
            f"- Safety: {top['safety_notes']}",
            f"- Confidence: {result.confidence:.0%}",
        ])

    if result.diagnostic_steps:
        lines.extend(["", "**Recommended Diagnostic Steps:**"])
        for step in result.diagnostic_steps[:4]:
            lines.append(f"{step['step_order']}. {step['description']}")

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