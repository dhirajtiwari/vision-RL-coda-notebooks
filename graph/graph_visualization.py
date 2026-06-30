"""
Interactive graph visualization payloads for Neo4j subgraphs and ontology schema.

Returns {nodes, edges} structures suitable for PyVis / D3 / neovis.js and embeds
the same reasoning paths shown in Neo4j Browser tutorials.
"""

from __future__ import annotations

from typing import Any

from graph.neo4j_client import get_driver

NODE_COLORS = {
    "Product": "#5B9BD5",
    "Model": "#2E75B6",
    "SKU": "#4472C4",
    "Symptom": "#FFC000",
    "FailureMode": "#70AD47",
    "DiagnosticStep": "#9E7FD0",
    "Component": "#00B0F0",
    "Part": "#A5A5A5",
    "ErrorCode": "#FF6600",
    "Asset": "#C55A11",
    "Claim": "#843C0C",
    "HistoricalResolution": "#ED7D31",
    "SchemaLabel": "#1F4E79",
}

NODE_SHAPES = {
    "Product": "box",
    "Symptom": "ellipse",
    "FailureMode": "box",
    "DiagnosticStep": "box",
    "Part": "box",
    "HistoricalResolution": "box",
    "SchemaLabel": "box",
}


def _node_key(label: str, entity_id: str) -> str:
    return f"{label}:{entity_id}"


def _add_node(
    nodes: dict[str, dict[str, Any]],
    label: str,
    entity_id: str,
    title: str,
    *,
    highlight: bool = False,
) -> str:
    key = _node_key(label, entity_id)
    if key not in nodes:
        nodes[key] = {
            "id": key,
            "label": label,
            "entity_id": entity_id,
            "title": title,
            "color": NODE_COLORS.get(label, "#CCCCCC"),
            "shape": NODE_SHAPES.get(label, "dot"),
            "highlight": highlight,
        }
    elif highlight:
        nodes[key]["highlight"] = True
    return key


def _add_edge(
    edges: list[dict[str, Any]],
    source: str,
    target: str,
    rel_type: str,
    *,
    properties: dict[str, Any] | None = None,
    highlight: bool = False,
) -> None:
    edge_id = f"{source}|{rel_type}|{target}"
    if any(e["id"] == edge_id for e in edges):
        return
    edges.append({
        "id": edge_id,
        "source": source,
        "target": target,
        "type": rel_type,
        "label": rel_type,
        "properties": properties or {},
        "highlight": highlight,
    })


def graph_payload(nodes: dict[str, dict[str, Any]], edges: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "nodes": list(nodes.values()),
        "edges": edges,
        "node_count": len(nodes),
        "edge_count": len(edges),
    }


def get_ontology_schema() -> dict[str, Any]:
    """ER-style meta-graph of node labels and relationship types (no Neo4j query)."""
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []

    labels = [
        ("Product", "product_id · name · category · brand"),
        ("Model", "model_id · model_number"),
        ("SKU", "sku_id · revision · model_year"),
        ("Asset", "asset_id · serial_number · model_number"),
        ("Symptom", "symptom_id · description · severity"),
        ("ErrorCode", "code · description"),
        ("FailureMode", "failure_mode_id · name · repair_minutes"),
        ("DiagnosticStep", "step_id · description · order"),
        ("Component", "component_id · subsystem"),
        ("Part", "part_id · name · part_number · cost"),
        ("Claim", "claim_id · resolution_summary"),
        ("HistoricalResolution", "resolution_id · description · date"),
    ]
    for label, props in labels:
        _add_node(nodes, "SchemaLabel", label, f":{label}\n{props}")

    rels = [
        ("Product", "Model", "HAS_MODEL"),
        ("Model", "SKU", "HAS_SKU"),
        ("Asset", "SKU", "BOUND_TO_SKU"),
        ("Asset", "Product", "INSTANCE_OF"),
        ("Product", "Symptom", "HAS_SYMPTOM"),
        ("Product", "ErrorCode", "HAS_ERROR_CODE"),
        ("ErrorCode", "FailureMode", "INDICATES"),
        ("Product", "FailureMode", "CAN_HAVE"),
        ("Product", "DiagnosticStep", "HAS_DIAGNOSTIC_STEP"),
        ("DiagnosticStep", "FailureMode", "CONFIRMS"),
        ("Symptom", "FailureMode", "INDICATES {confidence}"),
        ("FailureMode", "Component", "IMPACTS_COMPONENT"),
        ("Component", "Part", "REALIZED_BY"),
        ("FailureMode", "Part", "REQUIRES_PART {qty, probability}"),
        ("SKU", "Part", "COMPATIBLE_WITH"),
        ("Claim", "FailureMode", "CONFIRMED"),
        ("Claim", "Part", "USED_PART"),
        ("HistoricalResolution", "Product", "FOR_PRODUCT"),
        ("HistoricalResolution", "FailureMode", "CONFIRMED"),
    ]
    for src, tgt, rel in rels:
        _add_edge(
            edges,
            _node_key("SchemaLabel", src),
            _node_key("SchemaLabel", tgt),
            rel,
        )

    return graph_payload(nodes, edges)


def get_product_subgraph(product_id: str) -> dict[str, Any]:
    """Full product neighborhood — equivalent to exploring a product in Neo4j Browser."""
    driver = get_driver()
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []

    with driver.session() as session:
        product = session.run(
            """
            MATCH (p:Product {product_id: $product_id})
            RETURN p.product_id AS product_id, p.name AS name,
                   p.category AS category, p.brand AS brand
            """,
            product_id=product_id,
        ).single()
        if not product:
            return graph_payload(nodes, edges)

        pid = product["product_id"]
        _add_node(
            nodes, "Product", pid,
            f"{product['name']}\n{product['brand']} · {product['category']}",
        )

        for row in session.run(
            """
            MATCH (p:Product {product_id: $product_id})-[:HAS_SYMPTOM]->(s:Symptom)
            RETURN s.symptom_id AS symptom_id, s.description AS description,
                   s.severity AS severity
            """,
            product_id=product_id,
        ):
            sid = row["symptom_id"]
            s_key = _add_node(
                nodes, "Symptom", sid,
                f"{row['description']}\n[{row['severity']}]",
            )
            _add_edge(edges, _node_key("Product", pid), s_key, "HAS_SYMPTOM")

        for row in session.run(
            """
            MATCH (p:Product {product_id: $product_id})-[:CAN_HAVE]->(fm:FailureMode)
            RETURN fm.failure_mode_id AS failure_mode_id, fm.name AS name,
                   fm.description AS description
            """,
            product_id=product_id,
        ):
            fid = row["failure_mode_id"]
            fm_key = _add_node(nodes, "FailureMode", fid, f"{row['name']}\n{row['description'][:60]}")
            _add_edge(edges, _node_key("Product", pid), fm_key, "CAN_HAVE")

        for row in session.run(
            """
            MATCH (p:Product {product_id: $product_id})-[:HAS_DIAGNOSTIC_STEP]->(ds:DiagnosticStep)
            RETURN ds.step_id AS step_id, ds.description AS description, ds.order AS step_order
            ORDER BY ds.order
            """,
            product_id=product_id,
        ):
            did = row["step_id"]
            ds_key = _add_node(
                nodes, "DiagnosticStep", did,
                f"Step {row['step_order']}: {row['description'][:50]}",
            )
            _add_edge(edges, _node_key("Product", pid), ds_key, "HAS_DIAGNOSTIC_STEP")

        for row in session.run(
            """
            MATCH (p:Product {product_id: $product_id})-[:CAN_HAVE]->(fm:FailureMode)
                  -[:REQUIRES_PART]->(pt:Part)
            RETURN fm.failure_mode_id AS failure_mode_id, pt.part_id AS part_id,
                   pt.name AS name, pt.part_number AS part_number,
                   pt.estimated_cost_usd AS cost
            """,
            product_id=product_id,
        ):
            fid, ptid = row["failure_mode_id"], row["part_id"]
            fm_key = _node_key("FailureMode", fid)
            pt_key = _add_node(
                nodes, "Part", ptid,
                f"{row['name']}\n{row['part_number']} · ${row['cost']}",
            )
            _add_edge(edges, fm_key, pt_key, "REQUIRES_PART")

        for row in session.run(
            """
            MATCH (s:Symptom)-[ind:INDICATES]->(fm:FailureMode)
            MATCH (p:Product {product_id: $product_id})-[:HAS_SYMPTOM]->(s)
            MATCH (p)-[:CAN_HAVE]->(fm)
            RETURN s.symptom_id AS symptom_id, fm.failure_mode_id AS failure_mode_id,
                   ind.confidence AS confidence
            """,
            product_id=product_id,
        ):
            s_key = _node_key("Symptom", row["symptom_id"])
            fm_key = _node_key("FailureMode", row["failure_mode_id"])
            _add_edge(
                edges, s_key, fm_key, "INDICATES",
                properties={"confidence": row["confidence"]},
            )

        for row in session.run(
            """
            MATCH (r:HistoricalResolution)-[:FOR_PRODUCT]->(p:Product {product_id: $product_id})
            OPTIONAL MATCH (r)-[:CONFIRMED]->(fm:FailureMode)
            RETURN r.resolution_id AS resolution_id, r.description AS description,
                   r.resolution_date AS resolution_date, fm.failure_mode_id AS failure_mode_id
            """,
            product_id=product_id,
        ):
            rid = row["resolution_id"]
            r_key = _add_node(
                nodes, "HistoricalResolution", rid,
                f"{row['description'][:50]}\n{row['resolution_date']}",
            )
            _add_edge(edges, r_key, _node_key("Product", pid), "FOR_PRODUCT")
            if row["failure_mode_id"]:
                _add_edge(edges, r_key, _node_key("FailureMode", row["failure_mode_id"]), "CONFIRMED")

    return graph_payload(nodes, edges)


def get_diagnosis_subgraph(
    product_id: str,
    symptom_ids: list[str] | None = None,
    failure_mode_id: str | None = None,
    *,
    include_steps: bool = True,
    include_resolutions: bool = True,
) -> dict[str, Any]:
    """
    Subgraph for the reasoning path used during diagnosis — mirrors Cypher query
    results shown interactively in Neo4j tutorials when a chat/query fires.
    """
    driver = get_driver()
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []
    symptom_ids = symptom_ids or []

    with driver.session() as session:
        product = session.run(
            """
            MATCH (p:Product {product_id: $product_id})
            RETURN p.product_id AS product_id, p.name AS name
            """,
            product_id=product_id,
        ).single()
        if not product:
            return graph_payload(nodes, edges)

        pid = product["product_id"]
        p_key = _add_node(nodes, "Product", pid, product["name"], highlight=True)

        if symptom_ids:
            for row in session.run(
                """
                MATCH (p:Product {product_id: $product_id})-[:HAS_SYMPTOM]->(s:Symptom)
                WHERE s.symptom_id IN $symptom_ids
                RETURN s.symptom_id AS symptom_id, s.description AS description,
                       s.severity AS severity
                """,
                product_id=product_id,
                symptom_ids=symptom_ids,
            ):
                sid = row["symptom_id"]
                s_key = _add_node(
                    nodes, "Symptom", sid,
                    f"{row['description']}\n[{row['severity']}]",
                    highlight=True,
                )
                _add_edge(edges, p_key, s_key, "HAS_SYMPTOM", highlight=True)

        fm_query = """
            MATCH (p:Product {product_id: $product_id})-[:CAN_HAVE]->(fm:FailureMode)
        """
        params: dict[str, Any] = {"product_id": product_id}
        if failure_mode_id:
            fm_query += " WHERE fm.failure_mode_id = $failure_mode_id"
            params["failure_mode_id"] = failure_mode_id
        elif symptom_ids:
            fm_query += """
                WHERE EXISTS {
                    MATCH (s:Symptom)-[:INDICATES]->(fm)
                    WHERE s.symptom_id IN $symptom_ids
                }
            """
            params["symptom_ids"] = symptom_ids
        fm_query += """
            RETURN fm.failure_mode_id AS failure_mode_id, fm.name AS name,
                   fm.description AS description
        """
        failure_keys: list[str] = []
        for row in session.run(fm_query, **params):
            fid = row["failure_mode_id"]
            is_top = failure_mode_id == fid if failure_mode_id else len(failure_keys) == 0
            fm_key = _add_node(
                nodes, "FailureMode", fid,
                f"{row['name']}\n{row['description'][:60]}",
                highlight=is_top,
            )
            failure_keys.append(fm_key)
            _add_edge(edges, p_key, fm_key, "CAN_HAVE", highlight=is_top)

        if symptom_ids and failure_keys:
            for row in session.run(
                """
                MATCH (s:Symptom)-[ind:INDICATES]->(fm:FailureMode)
                WHERE s.symptom_id IN $symptom_ids
                  AND fm.failure_mode_id IN $failure_mode_ids
                RETURN s.symptom_id AS symptom_id, fm.failure_mode_id AS failure_mode_id,
                       ind.confidence AS confidence
                """,
                symptom_ids=symptom_ids,
                failure_mode_ids=[k.split(":", 1)[1] for k in failure_keys],
            ):
                s_key = _node_key("Symptom", row["symptom_id"])
                fm_key = _node_key("FailureMode", row["failure_mode_id"])
                is_top = failure_mode_id == row["failure_mode_id"] if failure_mode_id else False
                _add_edge(
                    edges, s_key, fm_key, "INDICATES",
                    properties={"confidence": row["confidence"]},
                    highlight=is_top or row["confidence"] >= 0.85,
                )

        if failure_mode_id:
            for row in session.run(
                """
                MATCH (fm:FailureMode {failure_mode_id: $failure_mode_id})-[:REQUIRES_PART]->(pt:Part)
                RETURN pt.part_id AS part_id, pt.name AS name,
                       pt.part_number AS part_number, pt.estimated_cost_usd AS cost
                """,
                failure_mode_id=failure_mode_id,
            ):
                pt_key = _add_node(
                    nodes, "Part", row["part_id"],
                    f"{row['name']}\n{row['part_number']} · ${row['cost']}",
                    highlight=True,
                )
                _add_edge(
                    edges, _node_key("FailureMode", failure_mode_id), pt_key,
                    "REQUIRES_PART", highlight=True,
                )

        if include_steps:
            for row in session.run(
                """
                MATCH (p:Product {product_id: $product_id})-[:HAS_DIAGNOSTIC_STEP]->(ds:DiagnosticStep)
                RETURN ds.step_id AS step_id, ds.description AS description, ds.order AS step_order
                ORDER BY ds.order LIMIT 4
                """,
                product_id=product_id,
            ):
                ds_key = _add_node(
                    nodes, "DiagnosticStep", row["step_id"],
                    f"Step {row['step_order']}: {row['description'][:45]}",
                )
                _add_edge(edges, p_key, ds_key, "HAS_DIAGNOSTIC_STEP")

        if include_resolutions and failure_mode_id:
            for row in session.run(
                """
                MATCH (r:HistoricalResolution)-[:FOR_PRODUCT]->(p:Product {product_id: $product_id})
                MATCH (r)-[:CONFIRMED]->(fm:FailureMode {failure_mode_id: $failure_mode_id})
                RETURN r.resolution_id AS resolution_id, r.description AS description,
                       r.resolution_date AS resolution_date
                LIMIT 2
                """,
                product_id=product_id,
                failure_mode_id=failure_mode_id,
            ):
                r_key = _add_node(
                    nodes, "HistoricalResolution", row["resolution_id"],
                    f"{row['description'][:45]}\n{row['resolution_date']}",
                    highlight=True,
                )
                _add_edge(edges, r_key, p_key, "FOR_PRODUCT", highlight=True)
                _add_edge(
                    edges, r_key, _node_key("FailureMode", failure_mode_id),
                    "CONFIRMED", highlight=True,
                )

    return graph_payload(nodes, edges)


def diagnosis_subgraph_from_result(diagnosis: dict[str, Any]) -> dict[str, Any]:
    """Build diagnosis subgraph from a diagnosis payload returned by GraphRAG."""
    product_id = diagnosis.get("product_id", "")
    if not product_id:
        return graph_payload({}, [])

    symptom_ids = [s["symptom_id"] for s in diagnosis.get("matched_symptoms", [])]
    top_fm = (diagnosis.get("ranked_failure_modes") or [None])[0]
    failure_mode_id = top_fm.get("failure_mode_id") if top_fm else None

    return get_diagnosis_subgraph(
        product_id,
        symptom_ids=symptom_ids,
        failure_mode_id=failure_mode_id,
    )


def render_pyvis_html(
    graph_data: dict[str, Any],
    *,
    height: str = "520px",
    title: str = "Knowledge Graph",
    physics: bool = True,
) -> str:
    """Render interactive force-directed graph HTML (Neo4j Browser–style)."""
    from pyvis.network import Network

    net = Network(
        height=height,
        width="100%",
        bgcolor="#ffffff",
        font_color="#333333",
        directed=True,
        notebook=False,
    )
    net.set_options("""
    {
      "nodes": {
        "font": {"size": 13, "face": "Arial"},
        "borderWidth": 2,
        "shadow": true
      },
      "edges": {
        "font": {"size": 11, "align": "middle"},
        "arrows": {"to": {"enabled": true, "scaleFactor": 0.6}},
        "smooth": {"type": "dynamic"},
        "shadow": false
      },
      "physics": {
        "enabled": %s,
        "solver": "forceAtlas2Based",
        "forceAtlas2Based": {
          "gravitationalConstant": -40,
          "centralGravity": 0.01,
          "springLength": 120,
          "springConstant": 0.08
        },
        "stabilization": {"iterations": 150}
      },
      "interaction": {
        "hover": true,
        "tooltipDelay": 120,
        "navigationButtons": true,
        "keyboard": true
      }
    }
    """ % ("true" if physics else "false"))

    for node in graph_data.get("nodes", []):
        color = node.get("color", "#CCCCCC")
        if node.get("highlight"):
            color = "#FF6B6B"
        label = node.get("entity_id") or node.get("label", "")
        net.add_node(
            node["id"],
            label=label,
            title=node.get("title", label),
            color=color,
            shape=node.get("shape", "dot"),
            borderWidth=3 if node.get("highlight") else 1,
        )

    for edge in graph_data.get("edges", []):
        props = edge.get("properties") or {}
        edge_label = edge.get("label", "")
        if "confidence" in props:
            edge_label = f"{edge_label} ({props['confidence']:.2f})"
        color = "#E74C3C" if edge.get("highlight") else "#7F8C8D"
        width = 3 if edge.get("highlight") else 1
        net.add_edge(
            edge["source"],
            edge["target"],
            label=edge_label,
            color=color,
            width=width,
        )

    return net.generate_html(notebook=False)