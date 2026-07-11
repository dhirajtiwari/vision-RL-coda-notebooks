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
from graph.provenance import manifest_provenance_for_entity


def _provenance_props(
    catalog: dict[str, Any],
    entity_id: str,
    entity_type: str,
) -> dict[str, Any]:
    if not settings.enable_provenance:
        return {}
    prov = catalog.get("provenance", {}).get(entity_id, {})
    if prov:
        return {k: v for k, v in prov.items() if v is not None}
    return manifest_provenance_for_entity(entity_type, entity_id)


def create_constraints(tx) -> None:
    for query in [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Product) REQUIRE p.product_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Symptom) REQUIRE s.symptom_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (fm:FailureMode) REQUIRE fm.failure_mode_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (ds:DiagnosticStep) REQUIRE ds.step_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Part) REQUIRE p.part_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (r:HistoricalResolution) REQUIRE r.resolution_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (m:Model) REQUIRE m.model_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (sku:SKU) REQUIRE sku.sku_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Component) REQUIRE c.component_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (ec:ErrorCode) REQUIRE ec.error_code_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (a:Asset) REQUIRE a.asset_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (wp:WarrantyPolicy) REQUIRE wp.policy_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (cl:Claim) REQUIRE cl.claim_id IS UNIQUE",
    ]:
        tx.run(query)


def populate_graph(driver, data: dict[str, Any], *, etl_batch_id: str | None = None) -> dict[str, int]:
    """Load catalog into Neo4j. Returns entity counts."""
    batch_id = etl_batch_id or data.get("etl_batch_id", "")
    counts = {
        "products": 0,
        "symptoms": 0,
        "failure_modes": 0,
        "steps": 0,
        "resolutions": 0,
        "models": 0,
        "skus": 0,
        "components": 0,
        "error_codes": 0,
        "assets": 0,
        "claims": 0,
        "policies": 0,
    }

    with driver.session() as session:
        session.execute_write(create_constraints)

        for product_data in data.get("products", []):
            product = product_data["product"]
            product_id = product["product_id"]
            p_prov = _provenance_props(data, product_id, "Product")

            session.run(
                """
                MERGE (p:Product {product_id: $product_id})
                SET p.name = $name, p.category = $category, p.brand = $brand,
                    p.model_year = $model_year, p.etl_batch_id = $etl_batch_id,
                    p.source_system = $source_system, p.source_record_id = $source_record_id,
                    p.source_document_uri = $source_document_uri, p.approval_status = $approval_status,
                    p.last_bulletin_id = $last_bulletin_id,
                    p.bulletin_revision = $bulletin_revision
                """,
                {
                    "product_id": product_id,
                    "name": product.get("name"),
                    "category": product.get("category"),
                    "brand": product.get("brand"),
                    "model_year": product.get("model_year"),
                    "last_bulletin_id": product.get("last_bulletin_id") or product.get("bulletin_id") or "",
                    "bulletin_revision": product.get("bulletin_revision") or "",
                    "etl_batch_id": batch_id,
                    **{
                        k: p_prov.get(k, "")
                        for k in ("source_system", "source_record_id", "source_document_uri", "approval_status")
                    },
                },
            )
            counts["products"] += 1

            for symptom in product_data.get("symptoms", []):
                sid = symptom["symptom_id"]
                s_prov = _provenance_props(data, sid, "Symptom")
                session.run(
                    """
                    MERGE (s:Symptom {symptom_id: $symptom_id})
                    SET s.description = $description, s.severity = $severity,
                        s.source_system = $source_system, s.source_record_id = $source_record_id,
                        s.source_document_uri = $source_document_uri, s.approval_status = $approval_status
                    """,
                    {
                        **symptom,
                        **{
                            k: s_prov.get(k, "")
                            for k in ("source_system", "source_record_id", "source_document_uri", "approval_status")
                        },
                    },
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
                f_prov = _provenance_props(data, fid, "FailureMode")
                session.run(
                    """
                    MERGE (fm:FailureMode {failure_mode_id: $failure_mode_id})
                    SET fm.name = $name, fm.description = $description,
                        fm.estimated_repair_time_minutes = $estimated_repair_time_minutes,
                        fm.safety_notes = $safety_notes,
                        fm.source_system = $source_system, fm.source_record_id = $source_record_id,
                        fm.source_document_uri = $source_document_uri
                    """,
                    {
                        **fm,
                        **{k: f_prov.get(k, "") for k in ("source_system", "source_record_id", "source_document_uri")},
                    },
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
                d_prov = _provenance_props(data, stid, "DiagnosticStep")
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
                pt_prov = _provenance_props(data, part["part_id"], "Part")
                session.run(
                    """
                    MERGE (pt:Part {part_id: $part_id})
                    SET pt.name = $name, pt.part_number = $part_number,
                        pt.estimated_cost_usd = $estimated_cost_usd,
                        pt.source_system = $source_system,
                        pt.source_record_id = $source_record_id,
                        pt.source_document_uri = $source_document_uri
                    """,
                    {
                        **part,
                        "source_system": pt_prov.get("source_system", ""),
                        "source_record_id": pt_prov.get("source_record_id", part["part_id"]),
                        "source_document_uri": pt_prov.get("source_document_uri", ""),
                    },
                )

            model = product_data.get("model")
            if model:
                # Multi-source packs may supply model_id + name/platform without
                # model_number (SKU carries the commercial model number). Default
                # so Cypher MERGE never fails with ParameterMissing.
                model_number = (
                    model.get("model_number")
                    or model.get("name")
                    or next(
                        (
                            s.get("model_number")
                            for s in product_data.get("skus", [])
                            if isinstance(s, dict) and s.get("model_number")
                        ),
                        None,
                    )
                    or model.get("model_id")
                    or ""
                )
                model_name = model.get("name") or model_number or model.get("model_id") or ""
                session.run(
                    """
                    MERGE (m:Model {model_id: $model_id})
                    SET m.model_number = $model_number, m.name = $name
                    """,
                    {
                        "model_id": model["model_id"],
                        "model_number": model_number,
                        "name": model_name,
                    },
                )
                session.run(
                    """
                    MATCH (p:Product {product_id: $product_id})
                    MATCH (m:Model {model_id: $model_id})
                    MERGE (p)-[:HAS_MODEL]->(m)
                    """,
                    {"product_id": product_id, "model_id": model["model_id"]},
                )
                counts["models"] += 1

            for sku in product_data.get("skus", []):
                session.run(
                    """
                    MERGE (sku:SKU {sku_id: $sku_id})
                    SET sku.revision = $revision, sku.model_year = $model_year,
                        sku.name = $name
                    """,
                    {
                        "sku_id": sku["sku_id"],
                        "revision": sku.get("revision") or "A",
                        "model_year": sku.get("model_year") or product.get("model_year") or 0,
                        "name": sku.get("name") or sku["sku_id"],
                    },
                )
                session.run(
                    """
                    MATCH (p:Product {product_id: $product_id})
                    MATCH (sku:SKU {sku_id: $sku_id})
                    MERGE (p)-[:HAS_SKU]->(sku)
                    """,
                    {"product_id": product_id, "sku_id": sku["sku_id"]},
                )
                if model:
                    session.run(
                        """
                        MATCH (m:Model {model_id: $model_id})
                        MATCH (sku:SKU {sku_id: $sku_id})
                        MERGE (m)-[:HAS_SKU]->(sku)
                        """,
                        {"model_id": model["model_id"], "sku_id": sku["sku_id"]},
                    )
                counts["skus"] += 1

            for comp in product_data.get("components", []):
                session.run(
                    """
                    MERGE (c:Component {component_id: $component_id})
                    SET c.name = $name, c.subsystem = $subsystem
                    """,
                    comp,
                )
                session.run(
                    """
                    MATCH (p:Product {product_id: $product_id})
                    MATCH (c:Component {component_id: $component_id})
                    MERGE (p)-[:HAS_COMPONENT]->(c)
                    """,
                    {"product_id": product_id, "component_id": comp["component_id"]},
                )
                counts["components"] += 1

            for link in product_data.get("component_part_links", []):
                session.run(
                    """
                    MATCH (c:Component {component_id: $component_id})
                    MATCH (pt:Part {part_id: $part_id})
                    MERGE (c)-[:REALIZED_BY]->(pt)
                    """,
                    link,
                )

            for link in product_data.get("failure_mode_component_links", []):
                session.run(
                    """
                    MATCH (fm:FailureMode {failure_mode_id: $failure_mode_id})
                    MATCH (c:Component {component_id: $component_id})
                    MERGE (fm)-[r:IMPACTS_COMPONENT]->(c)
                    SET r.impact_severity = $impact_severity
                    """,
                    {
                        "failure_mode_id": link["failure_mode_id"],
                        "component_id": link["component_id"],
                        "impact_severity": link.get("impact_severity") or "medium",
                    },
                )

            for ec in product_data.get("error_codes", []):
                session.run(
                    """
                    MERGE (ec:ErrorCode {error_code_id: $error_code_id})
                    SET ec.code = $code, ec.description = $description
                    """,
                    ec,
                )
                session.run(
                    """
                    MATCH (p:Product {product_id: $product_id})
                    MATCH (ec:ErrorCode {error_code_id: $error_code_id})
                    MERGE (p)-[:HAS_ERROR_CODE]->(ec)
                    """,
                    {"product_id": product_id, "error_code_id": ec["error_code_id"]},
                )
                counts["error_codes"] += 1

            for link in product_data.get("error_code_failure_links", []):
                session.run(
                    """
                    MATCH (ec:ErrorCode {error_code_id: $error_code_id})
                    MATCH (fm:FailureMode {failure_mode_id: $failure_mode_id})
                    MERGE (ec)-[r:INDICATES]->(fm)
                    SET r.confidence = $confidence
                    """,
                    {
                        "error_code_id": link["error_code_id"],
                        "failure_mode_id": link["failure_mode_id"],
                        "confidence": float(link.get("confidence", 0.8)),
                    },
                )

            for link in product_data.get("diagnostic_tree_links", []):
                session.run(
                    """
                    MATCH (a:DiagnosticStep {step_id: $from_step_id})
                    MATCH (b:DiagnosticStep {step_id: $to_step_id})
                    MERGE (a)-[r:NEXT_STEP]->(b)
                    SET r.condition = $condition
                    """,
                    {
                        "from_step_id": link["from_step_id"],
                        "to_step_id": link["to_step_id"],
                        "condition": link.get("condition") or "",
                    },
                )

            for link in product_data.get("diagnostic_step_failure_links", []):
                rel = link.get("link_type", "CONFIRMS")
                if rel not in ("CONFIRMS", "RULES_OUT"):
                    rel = "CONFIRMS"
                session.run(
                    f"""
                    MATCH (ds:DiagnosticStep {{step_id: $step_id}})
                    MATCH (fm:FailureMode {{failure_mode_id: $failure_mode_id}})
                    MERGE (ds)-[r:{rel}]->(fm)
                    SET r.confidence = $confidence
                    """,
                    {
                        "step_id": link["step_id"],
                        "failure_mode_id": link["failure_mode_id"],
                        "confidence": float(link.get("confidence", 0.85)),
                    },
                )

            for link in product_data.get("failure_mode_part_links", []):
                session.run(
                    """
                    MATCH (fm:FailureMode {failure_mode_id: $failure_mode_id})
                    MATCH (pt:Part {part_id: $part_id})
                    MERGE (fm)-[r:REQUIRES_PART]->(pt)
                    SET r.quantity = $quantity, r.probability = $probability, r.is_primary = $is_primary
                    """,
                    {
                        **link,
                        "quantity": link.get("quantity", 1),
                        "probability": link.get("probability", 0.9),
                        "is_primary": link.get("is_primary", True),
                    },
                )

            for link in product_data.get("sku_part_links", []):
                session.run(
                    """
                    MATCH (sku:SKU {sku_id: $sku_id})
                    MATCH (pt:Part {part_id: $part_id})
                    MERGE (sku)-[:COMPATIBLE_WITH]->(pt)
                    """,
                    link,
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
                r_prov = _provenance_props(data, rid, "HistoricalResolution")
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

        for policy in data.get("warranty_policies", []):
            session.run(
                """
                MERGE (wp:WarrantyPolicy {policy_id: $policy_id})
                SET wp.description = $description, wp.coverage_months = $coverage_months,
                    wp.covers_parts = $covers_parts, wp.covers_labor = $covers_labor,
                    wp.max_parts_cost_usd = $max_parts_cost_usd
                """,
                policy,
            )
            counts["policies"] += 1

        for asset in data.get("assets", []):
            session.run(
                """
                MERGE (a:Asset {asset_id: $asset_id})
                SET a.customer_id = $customer_id, a.serial_number = $serial_number,
                    a.model_number = $model_number, a.purchase_date = $purchase_date,
                    a.warranty_status = $warranty_status, a.warranty_expiry = $warranty_expiry
                """,
                asset,
            )
            session.run(
                """
                MATCH (a:Asset {asset_id: $asset_id})
                MATCH (p:Product {product_id: $product_id})
                MERGE (a)-[:INSTANCE_OF]->(p)
                """,
                {"asset_id": asset["asset_id"], "product_id": asset["product_id"]},
            )
            if asset.get("sku_id"):
                session.run(
                    """
                    MATCH (a:Asset {asset_id: $asset_id})
                    MATCH (sku:SKU {sku_id: $sku_id})
                    MERGE (a)-[:BOUND_TO_SKU]->(sku)
                    """,
                    {"asset_id": asset["asset_id"], "sku_id": asset["sku_id"]},
                )
            if asset.get("policy_id"):
                session.run(
                    """
                    MATCH (a:Asset {asset_id: $asset_id})
                    MATCH (wp:WarrantyPolicy {policy_id: $policy_id})
                    MERGE (a)-[:COVERED_BY]->(wp)
                    """,
                    {"asset_id": asset["asset_id"], "policy_id": asset["policy_id"]},
                )
                session.run(
                    """
                    MATCH (wp:WarrantyPolicy {policy_id: $policy_id})
                    MATCH (p:Product {product_id: $product_id})
                    MERGE (wp)-[:COVERS_PRODUCT]->(p)
                    """,
                    {"policy_id": asset["policy_id"], "product_id": asset["product_id"]},
                )
            counts["assets"] += 1

        for claim in data.get("claims", []):
            session.run(
                """
                MERGE (cl:Claim {claim_id: $claim_id})
                SET cl.resolution_summary = $resolution_summary, cl.closed_date = $closed_date,
                    cl.symptom_id = $symptom_id
                """,
                claim,
            )
            session.run(
                """
                MATCH (cl:Claim {claim_id: $claim_id})
                MATCH (a:Asset {asset_id: $asset_id})
                MERGE (cl)-[:FOR_ASSET]->(a)
                """,
                {"claim_id": claim["claim_id"], "asset_id": claim["asset_id"]},
            )
            session.run(
                """
                MATCH (cl:Claim {claim_id: $claim_id})
                MATCH (fm:FailureMode {failure_mode_id: $confirmed_failure_mode_id})
                MERGE (cl)-[:CONFIRMED]->(fm)
                """,
                claim,
            )
            if claim.get("used_part_id"):
                session.run(
                    """
                    MATCH (cl:Claim {claim_id: $claim_id})
                    MATCH (pt:Part {part_id: $used_part_id})
                    MERGE (cl)-[:USED_PART]->(pt)
                    """,
                    claim,
                )
            counts["claims"] += 1

    return counts


def load_from_file(path: Path | None = None) -> dict[str, int]:
    path = path or settings.data_file
    data = json.loads(path.read_text(encoding="utf-8"))
    from graph.neo4j_client import close_driver

    driver = get_driver()
    try:
        return populate_graph(driver, data)
    finally:
        close_driver()


if __name__ == "__main__":
    print("Loading knowledge graph into Neo4j...")
    counts = load_from_file()
    print(f"Loaded: {counts}")
