"""Product-level knowledge lineage from Neo4j — how ontology was built for a product."""

from __future__ import annotations

from typing import Any

from graph.neo4j_client import get_driver


def get_product_knowledge_profile(product_id: str) -> dict[str, Any] | None:
    """Aggregate counts and source-system breakdown for a product's graph knowledge."""
    driver = get_driver()
    with driver.session() as session:
        row = session.run(
            """
            MATCH (p:Product {product_id: $product_id})
            OPTIONAL MATCH (p)-[:HAS_SYMPTOM]->(s:Symptom)
            OPTIONAL MATCH (p)-[:CAN_HAVE]->(fm:FailureMode)
            OPTIONAL MATCH (p)-[:HAS_DIAGNOSTIC_STEP]->(ds:DiagnosticStep)
            OPTIONAL MATCH (fm2:FailureMode)<-[:CAN_HAVE]-(p)
            OPTIONAL MATCH (fm2)-[:REQUIRES_PART]->(pt:Part)
            RETURN p.product_id AS product_id,
                   p.name AS product_name,
                   p.brand AS brand,
                   p.category AS category,
                   p.etl_batch_id AS etl_batch_id,
                   p.source_system AS product_source,
                   count(DISTINCT s) AS symptom_count,
                   count(DISTINCT fm) AS failure_mode_count,
                   count(DISTINCT ds) AS step_count,
                   count(DISTINCT pt) AS part_count
            """,
            product_id=product_id,
        ).single()
        if not row:
            return None
        profile = dict(row)

        source_counts: dict[str, int] = {}
        for label, _prop in (
            ("Symptom", "s"),
            ("FailureMode", "fm"),
            ("DiagnosticStep", "ds"),
            ("Part", "pt"),
        ):
            query = f"""
                MATCH (p:Product {{product_id: $product_id}})
                MATCH (p)-[*0..2]-(n:{label})
                WHERE n.source_system IS NOT NULL AND n.source_system <> ''
                RETURN n.source_system AS src, count(DISTINCT n) AS cnt
            """
            if label == "Part":
                query = """
                    MATCH (p:Product {product_id: $product_id})-[:CAN_HAVE]->(fm:FailureMode)
                    MATCH (fm)-[:REQUIRES_PART]->(pt:Part)
                    WHERE pt.source_system IS NOT NULL AND pt.source_system <> ''
                    RETURN pt.source_system AS src, count(DISTINCT pt) AS cnt
                """
            elif label == "FailureMode":
                query = """
                    MATCH (p:Product {product_id: $product_id})-[:CAN_HAVE]->(fm:FailureMode)
                    WHERE fm.source_system IS NOT NULL AND fm.source_system <> ''
                    RETURN fm.source_system AS src, count(DISTINCT fm) AS cnt
                """
            elif label == "Symptom":
                query = """
                    MATCH (p:Product {product_id: $product_id})-[:HAS_SYMPTOM]->(s:Symptom)
                    WHERE s.source_system IS NOT NULL AND s.source_system <> ''
                    RETURN s.source_system AS src, count(DISTINCT s) AS cnt
                """
            else:
                query = """
                    MATCH (p:Product {product_id: $product_id})-[:HAS_DIAGNOSTIC_STEP]->(ds:DiagnosticStep)
                    WHERE ds.source_system IS NOT NULL AND ds.source_system <> ''
                    RETURN ds.source_system AS src, count(DISTINCT ds) AS cnt
                """
            for r in session.run(query, product_id=product_id):
                src = r["src"] or "Synthetic"
                source_counts[src] = source_counts.get(src, 0) + int(r["cnt"])

        if not source_counts:
            source_counts = {
                "PIM": int(profile.get("symptom_count") or 0),
                "FMEA": int(profile.get("failure_mode_count") or 0),
                "ServiceManual": int(profile.get("step_count") or 0),
            }

        profile["source_counts"] = source_counts
        return profile
