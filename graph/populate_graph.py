"""
Neo4j Knowledge Graph Loader
Loads validated ontology catalog into Neo4j with MERGE and optional provenance metadata.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from config.settings import settings
from graph.neo4j_client import get_driver


def _provenance_props(catalog: dict[str, Any], entity_id: str) -> dict[str, Any]:
    if not settings.enable_provenance:
        return {}
    prov = catalog.get("provenance", {}).get(entity_id, {})
    if not prov:
        return {}
    return {k: v for k, v in prov.items() if v is not None}


def create_constraints(tx) -> None:
    for query in [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Product) REQUIRE p.product_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Symptom) REQUIRE s.symptom_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (fm:FailureMode) REQUIRE fm.failure_mode_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (ds:DiagnosticStep) REQUIRE ds.step_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Part) REQUIRE p.part_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (r:HistoricalResolution) REQUIRE r.resolution_id IS UNIQUE",
    ]:
        tx.run(query)


def populate_graph(driver, data: dict[str, Any], *, etl_batch_id: str | None = None) -> dict[str, int]:
    """Load catalog into Neo4j. Returns entity counts."""
    batch_id = etl_batch_id or data.get("etl_batch_id", "")
    counts = {"products": 0, "symptoms": 0, "failure_modes": 0, "steps": 0, "resolutions": 0}

    with driver.session() as session:
        session.execute_write(create_constraints)

        for product_data in data.get("products", []):
            product = product_data["product"]
            product_id = product["product_id"]
            p_prov = _provenance_props(data, product_id)

            session.run(
                """
                MERGE (p:Product {product_id: $product_id})
                SET p.name = $name, p.category = $category, p.brand = $brand,
                    p.model_year = $model_year, p.etl_batch_id = $etl_batch_id,
                    p.source_system = $source_system, p.source_record_id = $source_record_id,
                    p.source_document_uri = $source_document_uri, p.approval_status = $approval_status
                """,
                {**product, "etl_batch_id": batch_id, **{k: p_prov.get(k, "") for k in (
                    "source_system", "source_record_id", "source_document_uri", "approval_status"
                )}},
            )
            counts["products"] += 1

            for symptom in product_data.get("symptoms", []):
                sid = symptom["symptom_id"]
                s_prov = _provenance_props(data, sid)
                session.run(
                    """
                    MERGE (s:Symptom {symptom_id: $symptom_id})
                    SET s.description = $description, s.severity = $severity,
                        s.source_system = $source_system, s.source_record_id = $source_record_id,
                        s.source_document_uri = $source_document_uri, s.approval_status = $approval_status
                    """,
                    {**symptom, **{k: s_prov.get(k, "") for k in (
                        "source_system", "source_record_id", "source_document_uri", "approval_status"
                    )}},
                )
                session.run(
                    """
                    MATCH (p:Product {product_id: $product_id})
                    MATCH (s:Symptom {symptom_id: $symptom_id})
                    MERGE (p)-[:HAS_SYMPTOM]->(s)
                    """,
                    {"product_id": product_id, "symptom_id": sid},
                )
                counts["symptoms"] += 1

            for fm in product_data.get("failure_modes", []):
                fid = fm["failure_mode_id"]
                f_prov = _provenance_props(data, fid)
                session.run(
                    """
                    MERGE (fm:FailureMode {failure_mode_id: $failure_mode_id})
                    SET fm.name = $name, fm.description = $description,
                        fm.estimated_repair_time_minutes = $estimated_repair_time_minutes,
                        fm.safety_notes = $safety_notes,
                        fm.source_system = $source_system, fm.source_record_id = $source_record_id,
                        fm.source_document_uri = $source_document_uri
                    """,
                    {**fm, **{k: f_prov.get(k, "") for k in (
                        "source_system", "source_record_id", "source_document_uri"
                    )}},
                )
                session.run(
                    """
                    MATCH (p:Product {product_id: $product_id})
                    MATCH (fm:FailureMode {failure_mode_id: $failure_mode_id})
                    MERGE (p)-[:CAN_HAVE]->(fm)
                    """,
                    {"product_id": product_id, "failure_mode_id": fid},
                )
                counts["failure_modes"] += 1

            for step in product_data.get("diagnostic_steps", []):
                stid = step["step_id"]
                d_prov = _provenance_props(data, stid)
                session.run(
                    """
                    MERGE (ds:DiagnosticStep {step_id: $step_id})
                    SET ds.description = $description, ds.order = $order,
                        ds.expected_outcome = $expected_outcome,
                        ds.source_system = $source_system, ds.source_document_uri = $source_document_uri
                    """,
                    {**step, **{k: d_prov.get(k, "") for k in ("source_system", "source_document_uri")}},
                )
                session.run(
                    """
                    MATCH (p:Product {product_id: $product_id})
                    MATCH (ds:DiagnosticStep {step_id: $step_id})
                    MERGE (p)-[:HAS_DIAGNOSTIC_STEP]->(ds)
                    """,
                    {"product_id": product_id, "step_id": stid},
                )
                counts["steps"] += 1

            for part in product_data.get("parts", []):
                pt_prov = _provenance_props(data, part["part_id"])
                session.run(
                    """
                    MERGE (pt:Part {part_id: $part_id})
                    SET pt.name = $name, pt.part_number = $part_number,
                        pt.estimated_cost_usd = $estimated_cost_usd,
                        pt.source_system = $source_system
                    """,
                    {**part, "source_system": pt_prov.get("source_system", "")},
                )

            for link in product_data.get("symptom_failure_links", []):
                session.run(
                    """
                    MATCH (s:Symptom {symptom_id: $symptom_id})
                    MATCH (fm:FailureMode {failure_mode_id: $failure_mode_id})
                    MERGE (s)-[r:INDICATES]->(fm)
                    SET r.confidence = $confidence, r.etl_batch_id = $etl_batch_id
                    """,
                    {**link, "etl_batch_id": batch_id},
                )

            for resolution in product_data.get("historical_resolutions", []):
                rid = resolution["resolution_id"]
                r_prov = _provenance_props(data, rid)
                session.run(
                    """
                    MERGE (r:HistoricalResolution {resolution_id: $resolution_id})
                    SET r.description = $description, r.resolution_date = $resolution_date,
                        r.technician_notes = $technician_notes,
                        r.source_system = $source_system, r.source_record_id = $source_record_id
                    """,
                    {
                        **resolution,
                        "source_system": r_prov.get("source_system", ""),
                        "source_record_id": r_prov.get("source_record_id", rid),
                    },
                )
                session.run(
                    """
                    MATCH (p:Product {product_id: $product_id})
                    MATCH (r:HistoricalResolution {resolution_id: $resolution_id})
                    MERGE (r)-[:FOR_PRODUCT]->(p)
                    """,
                    {"product_id": product_id, "resolution_id": rid},
                )
                session.run(
                    """
                    MATCH (r:HistoricalResolution {resolution_id: $resolution_id})
                    MATCH (fm:FailureMode {failure_mode_id: $failure_mode_id})
                    MERGE (r)-[:CONFIRMED]->(fm)
                    """,
                    {
                        "resolution_id": rid,
                        "failure_mode_id": resolution["confirmed_failure_mode_id"],
                    },
                )
                counts["resolutions"] += 1

    return counts


def load_from_file(path: Path | None = None) -> dict[str, int]:
    path = path or settings.data_file
    data = json.loads(path.read_text(encoding="utf-8"))
    driver = get_driver()
    try:
        return populate_graph(driver, data)
    finally:
        driver.close()


if __name__ == "__main__":
    print("Loading knowledge graph into Neo4j...")
    counts = load_from_file()
    print(f"Loaded: {counts}")