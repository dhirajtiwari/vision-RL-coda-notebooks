"""
Interactive graph visualization payloads for Neo4j subgraphs and ontology schema.

Returns {nodes, edges} structures suitable for PyVis / D3 / neovis.js and embeds
the same reasoning paths shown in Neo4j Browser tutorials.
"""

from __future__ import annotations

import html
import re
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
    edges.append(
        {
            "id": edge_id,
            "source": source,
            "target": target,
            "type": rel_type,
            "label": rel_type,
            "properties": properties or {},
            "highlight": highlight,
        }
    )


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
            nodes,
            "Product",
            pid,
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
                nodes,
                "Symptom",
                sid,
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
                nodes,
                "DiagnosticStep",
                did,
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
                nodes,
                "Part",
                ptid,
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
                edges,
                s_key,
                fm_key,
                "INDICATES",
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
                nodes,
                "HistoricalResolution",
                rid,
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
                    nodes,
                    "Symptom",
                    sid,
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
                nodes,
                "FailureMode",
                fid,
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
                    edges,
                    s_key,
                    fm_key,
                    "INDICATES",
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
                    nodes,
                    "Part",
                    row["part_id"],
                    f"{row['name']}\n{row['part_number']} · ${row['cost']}",
                    highlight=True,
                )
                _add_edge(
                    edges,
                    _node_key("FailureMode", failure_mode_id),
                    pt_key,
                    "REQUIRES_PART",
                    highlight=True,
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
                    nodes,
                    "DiagnosticStep",
                    row["step_id"],
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
                    nodes,
                    "HistoricalResolution",
                    row["resolution_id"],
                    f"{row['description'][:45]}\n{row['resolution_date']}",
                    highlight=True,
                )
                _add_edge(edges, r_key, p_key, "FOR_PRODUCT", highlight=True)
                _add_edge(
                    edges,
                    r_key,
                    _node_key("FailureMode", failure_mode_id),
                    "CONFIRMED",
                    highlight=True,
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


_LAYER_ORDER = {
    "Product": 0,
    "Symptom": 1,
    "FailureMode": 2,
    "Part": 3,
    "DiagnosticStep": 3,
    "HistoricalResolution": 4,
    "Component": 3,
}


def _executive_node_label(node: dict[str, Any]) -> str:
    """Business-readable label instead of raw entity IDs."""
    label = node.get("label", "")
    title = (node.get("title") or "").replace("\n", " · ")
    if label == "Product":
        return title.split("·")[0].strip() or node.get("entity_id", "Product")
    if label == "Symptom":
        return f"Symptom: {title[:55]}"
    if label == "FailureMode":
        return f"Cause: {title[:55]}"
    if label == "Part":
        return f"Part: {title[:50]}"
    if label == "DiagnosticStep":
        return f"Check: {title[:50]}"
    if label == "HistoricalResolution":
        return f"Prior fix: {title[:50]}"
    return title[:60] or node.get("entity_id", label)


_PATH_EDGE_TYPES = frozenset(
    {
        "HAS_SYMPTOM",
        "INDICATES",
        "CAN_HAVE",
        "REQUIRES_PART",
        "CONFIRMED",
        "FOR_PRODUCT",
    }
)


def filter_path_focus_graph(graph_data: dict[str, Any], *, path_only: bool = True) -> dict[str, Any]:
    """Keep only nodes and edges on the active diagnosis path for a cleaner executive view."""
    if not path_only:
        return graph_data

    nodes = graph_data.get("nodes") or []
    edges = graph_data.get("edges") or []
    if not nodes:
        return graph_data

    path_ids: set[str] = set()
    for node in nodes:
        if node.get("highlight") or node.get("label") == "Product":
            path_ids.add(node["id"])

    for edge in edges:
        if edge.get("highlight"):
            path_ids.add(edge["source"])
            path_ids.add(edge["target"])

    kept_nodes = [n for n in nodes if n["id"] in path_ids]
    kept_edges = [
        e
        for e in edges
        if e["source"] in path_ids
        and e["target"] in path_ids
        and (e.get("highlight") or e.get("type") in _PATH_EDGE_TYPES)
    ]
    return {
        **graph_data,
        "nodes": kept_nodes,
        "edges": kept_edges,
        "node_count": len(kept_nodes),
        "edge_count": len(kept_edges),
        "path_focus": True,
    }


def diagnosis_map_steps(diagnosis: dict[str, Any] | None) -> list[dict[str, str]]:
    """Ordered reasoning stages for the diagnosis map stepper."""
    if not diagnosis:
        return []

    product = diagnosis.get("product_name") or diagnosis.get("product_id") or "Product"
    symptoms = diagnosis.get("matched_symptoms") or []
    top_fm = (diagnosis.get("ranked_failure_modes") or [None])[0] or {}
    parts = diagnosis.get("predicted_parts") or diagnosis.get("parts") or []
    conf = diagnosis.get("confidence", 0)

    sym_text = symptoms[0].get("description", "—")[:48] if symptoms else "No symptom match"
    sym_score = f"{symptoms[0].get('match_score', 0):.0%}" if symptoms else "—"

    steps = [
        {"stage": "1", "label": "Product", "value": product, "meta": "Knowledge base"},
        {"stage": "2", "label": "Symptom", "value": sym_text, "meta": f"Match {sym_score}"},
        {
            "stage": "3",
            "label": "Root cause",
            "value": top_fm.get("name", "Under review"),
            "meta": f"Confidence {conf:.0%}",
        },
    ]
    if parts:
        part = parts[0]
        steps.append(
            {
                "stage": "4",
                "label": "Resolution",
                "value": part.get("name", "Part"),
                "meta": part.get("part_number", ""),
            }
        )
    resolutions = diagnosis.get("historical_resolutions") or []
    if resolutions:
        steps.append(
            {
                "stage": str(len(steps) + 1),
                "label": "Precedent",
                "value": (resolutions[0].get("description") or "")[:42],
                "meta": resolutions[0].get("resolution_date", ""),
            }
        )
    return steps


def ontology_mermaid_diagram() -> str:
    """Clean ER-style ontology diagram for executives and engineers."""
    return """erDiagram
    Product ||--o{ Model : HAS_MODEL
    Model ||--o{ SKU : HAS_SKU
    Asset }o--|| SKU : BOUND_TO_SKU
    Asset }o--|| Product : INSTANCE_OF
    Product ||--o{ Symptom : HAS_SYMPTOM
    Product ||--o{ ErrorCode : HAS_ERROR_CODE
    Product ||--o{ FailureMode : CAN_HAVE
    Product ||--o{ DiagnosticStep : HAS_DIAGNOSTIC_STEP
    Symptom }o--o{ FailureMode : INDICATES
    ErrorCode }o--o{ FailureMode : INDICATES
    DiagnosticStep }o--|| FailureMode : CONFIRMS
    FailureMode }o--o{ Component : IMPACTS_COMPONENT
    Component }o--o{ Part : REALIZED_BY
    FailureMode }o--o{ Part : REQUIRES_PART
    SKU }o--o{ Part : COMPATIBLE_WITH
    Claim }o--|| FailureMode : CONFIRMED
    Claim }o--o{ Part : USED_PART
    HistoricalResolution }o--|| Product : FOR_PRODUCT
    HistoricalResolution }o--o{ FailureMode : CONFIRMED"""


def product_graph_summary(graph_data: dict[str, Any]) -> dict[str, int]:
    """Count nodes by label for product explorer side panel."""
    counts: dict[str, int] = {}
    for node in graph_data.get("nodes", []):
        label = node.get("label", "Other")
        counts[label] = counts.get(label, 0) + 1
    return counts


def render_product_knowledge_html(
    graph_data: dict[str, Any],
    *,
    product_name: str = "Product",
    height: str = "520px",
) -> str:
    """Hierarchical product neighborhood map with summary header."""
    prepared = prepare_executive_graph(graph_data)
    net = _build_executive_pyvis_network(prepared, height=height)
    pyvis_raw = _sanitize_pyvis_html(net.generate_html(notebook=False))
    counts = product_graph_summary(graph_data)
    stats = " · ".join(f"{k} {v}" for k, v in sorted(counts.items()))

    chrome = f"""
<div class="pk-shell">
  <div class="pk-header">
    <div class="pk-title">Product knowledge map — {html.escape(product_name)}</div>
    <div class="pk-sub">Top-down view · {html.escape(stats)} · drag to pan, scroll to zoom</div>
  </div>
  <div class="pk-legend">
    <span><i style="background:#1e40af"></i>Product</span>
    <span><i style="background:#b45309"></i>Symptoms</span>
    <span><i style="background:#047857"></i>Failure modes</span>
    <span><i style="background:#334155"></i>Parts</span>
    <span><i style="background:#6d28d9"></i>Diagnostic steps</span>
    <span><i style="background:#c2410c"></i>Prior fixes</span>
  </div>
</div>
<style>
  .pk-shell {{ border: 1px solid #e2e8f0; border-radius: 12px 12px 0 0; overflow: hidden; background: #fff; }}
  .pk-header {{ padding: 14px 18px; border-bottom: 1px solid #e2e8f0; background: linear-gradient(180deg, #f8fafc 0%, #fff 100%); }}
  .pk-title {{ font-size: 15px; font-weight: 600; }}
  .pk-sub {{ font-size: 12px; color: #64748b; margin-top: 3px; }}
  .pk-legend {{ display: flex; flex-wrap: wrap; gap: 10px 16px; padding: 10px 18px; font-size: 11px; color: #475569; border-bottom: 1px solid #f1f5f9; }}
  .pk-legend span {{ display: inline-flex; align-items: center; gap: 6px; }}
  .pk-legend i {{ width: 10px; height: 10px; border-radius: 3px; display: inline-block; }}
  .graph-host {{ background: #fff; border: 1px solid #e2e8f0; border-top: none; border-radius: 0 0 12px 12px; }}
</style>"""
    return _compose_pyvis_shell(chrome, pyvis_raw)


def prepare_executive_graph(graph_data: dict[str, Any]) -> dict[str, Any]:
    """Annotate subgraph with executive labels and layer ranks for hierarchical layout."""
    nodes = []
    for node in graph_data.get("nodes", []):
        n = dict(node)
        n["executive_label"] = _executive_node_label(n)
        n["layer"] = _LAYER_ORDER.get(n.get("label", ""), 2)
        nodes.append(n)
    return {
        **graph_data,
        "nodes": nodes,
        "layout": "hierarchical",
    }


def _build_executive_pyvis_network(
    prepared: dict[str, Any],
    *,
    height: str = "520px",
) -> Any:
    from pyvis.network import Network

    net = Network(
        height=height,
        width="100%",
        bgcolor="#ffffff",
        font_color="#0f172a",
        directed=True,
        notebook=False,
    )
    net.set_options("""
    {
      "nodes": {
        "font": {"size": 13, "face": "Inter, Segoe UI, system-ui, sans-serif", "color": "#0f172a"},
        "borderWidth": 2,
        "margin": 14,
        "shapeProperties": {"borderRadius": 8}
      },
      "edges": {
        "font": {"size": 10, "align": "middle", "color": "#64748b"},
        "arrows": {"to": {"enabled": true, "scaleFactor": 0.45}},
        "smooth": {"type": "cubicBezier", "roundness": 0.35},
        "color": {"inherit": false}
      },
      "layout": {
        "hierarchical": {
          "enabled": true,
          "direction": "UD",
          "sortMethod": "directed",
          "levelSeparation": 160,
          "nodeSpacing": 200,
          "treeSpacing": 220
        }
      },
      "physics": {"enabled": false},
      "interaction": {
        "hover": true,
        "tooltipDelay": 80,
        "navigationButtons": false,
        "zoomView": true,
        "dragView": true
      }
    }
    """)

    _SHAPE = {
        "Product": "box",
        "Symptom": "ellipse",
        "FailureMode": "box",
        "Part": "box",
        "DiagnosticStep": "box",
        "HistoricalResolution": "box",
    }
    _TYPE_COLORS = {
        "Product": {"bg": "#dbeafe", "border": "#1d4ed8", "path": "#1e40af"},
        "Symptom": {"bg": "#fef3c7", "border": "#d97706", "path": "#b45309"},
        "FailureMode": {"bg": "#d1fae5", "border": "#059669", "path": "#047857"},
        "Part": {"bg": "#e2e8f0", "border": "#64748b", "path": "#334155"},
        "DiagnosticStep": {"bg": "#ede9fe", "border": "#7c3aed", "path": "#6d28d9"},
        "HistoricalResolution": {"bg": "#ffedd5", "border": "#ea580c", "path": "#c2410c"},
    }

    for node in prepared.get("nodes", []):
        ntype = node.get("label", "")
        is_path = node.get("highlight", False)
        palette = _TYPE_COLORS.get(ntype, {"bg": "#f1f5f9", "border": "#94a3b8", "path": "#475569"})
        fill = palette["path"] if is_path else palette["bg"]
        border = palette["path"] if is_path else palette["border"]
        font_color = "#ffffff" if is_path else "#0f172a"
        net.add_node(
            node["id"],
            label=node.get("executive_label", node.get("entity_id", "")),
            title=f"{ntype}\n{node.get('title', '')}",
            color={"background": fill, "border": border, "highlight": {"background": fill, "border": border}},
            font={"color": font_color, "size": 13 if is_path else 12},
            shape=_SHAPE.get(ntype, "dot"),
            borderWidth=3 if is_path else 1,
            size=28 if is_path else 22,
            level=node.get("layer", 2),
        )

    for edge in prepared.get("edges", []):
        props = edge.get("properties") or {}
        rel = edge.get("type", edge.get("label", ""))
        elabel = rel.replace("_", " ").title()
        if "confidence" in props:
            elabel = f"{elabel} · {props['confidence']:.0%}"
        is_path = edge.get("highlight", False)
        net.add_edge(
            edge["source"],
            edge["target"],
            label=elabel if is_path else "",
            color="#047857" if is_path else "#cbd5e1",
            width=3 if is_path else 1,
            dashes=not is_path,
        )

    return net


def _sanitize_pyvis_html(pyvis_html: str) -> str:
    """Return a self-contained pyvis document (fixes broken relative bindings path)."""
    cleaned = pyvis_html.replace('<script src="lib/bindings/utils.js"></script>', "")
    cleaned = cleaned.replace("<script src='lib/bindings/utils.js'></script>", "")
    return cleaned


def _pyvis_head_assets(pyvis_html: str) -> str:
    """Extract vis-network JS/CSS and #mynetwork styles required for rendering."""
    head_match = re.search(r"<head[^>]*>(.*)</head>", pyvis_html, re.DOTALL | re.IGNORECASE)
    head_content = head_match.group(1) if head_match else ""
    body_match = re.search(r"<body[^>]*>(.*)</body>", pyvis_html, re.DOTALL | re.IGNORECASE)
    body_content = body_match.group(1) if body_match else ""

    chunks: list[str] = []
    for source in (head_content, body_content):
        chunks.extend(re.findall(r"<link[^>]*vis-network[^>]*/?>", source, re.IGNORECASE))
        chunks.extend(re.findall(r"<script[^>]*vis-network[^>]*>.*?</script>", source, re.DOTALL | re.IGNORECASE))
        chunks.extend(re.findall(r"<style[^>]*>[\s\S]*?#mynetwork[\s\S]*?</style>", source, re.IGNORECASE))

    seen: set[str] = set()
    unique = []
    for chunk in chunks:
        key = chunk[:120]
        if key not in seen:
            seen.add(key)
            unique.append(chunk)
    return "\n".join(unique)


def _pyvis_body_content(pyvis_html: str) -> str:
    body_match = re.search(r"<body[^>]*>(.*)</body>", pyvis_html, re.DOTALL | re.IGNORECASE)
    body = body_match.group(1).strip() if body_match else pyvis_html
    return body.replace('<script src="lib/bindings/utils.js"></script>', "")


def _compose_pyvis_shell(chrome_html: str, pyvis_html: str) -> str:
    """Wrap pyvis graph with UI chrome while keeping vis.js assets in <head>."""
    assets = _pyvis_head_assets(pyvis_html)
    graph_body = _pyvis_body_content(pyvis_html)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
{assets}
<style>
  body {{ margin: 0; font-family: Inter, "Segoe UI", system-ui, sans-serif; background: #f8fafc; }}
  .graph-host #mynetwork {{ width: 100% !important; border: none !important; position: relative !important; float: none !important; }}
</style>
</head>
<body>
{chrome_html}
<div class="graph-host">{graph_body}</div>
</body>
</html>"""


def standalone_pyvis_html(
    graph_data: dict[str, Any],
    *,
    height: str = "520px",
    hierarchical: bool = True,
) -> str:
    """Full self-contained pyvis document for Streamlit components.html."""
    if hierarchical:
        prepared = prepare_executive_graph(graph_data)
        net = _build_executive_pyvis_network(prepared, height=height)
    else:
        net = _build_pyvis_network(graph_data, height=height)
    return _sanitize_pyvis_html(net.generate_html(notebook=False))


def _build_pyvis_network(graph_data: dict[str, Any], *, height: str = "520px") -> Any:
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
      "physics": {"enabled": false},
      "interaction": {"navigationButtons": true, "hover": true}
    }
    """)
    for node in graph_data.get("nodes", []):
        net.add_node(
            node["id"],
            label=node.get("entity_id") or node.get("label", ""),
            title=node.get("title", ""),
            color=node.get("color", "#CCCCCC"),
            shape=node.get("shape", "dot"),
        )
    for edge in graph_data.get("edges", []):
        net.add_edge(edge["source"], edge["target"], label=edge.get("label", ""))
    return net


def render_mermaid_html(mermaid_source: str, *, title: str = "Diagram") -> str:
    """Render Mermaid in a polished, scrollable iframe-friendly shell.

    Improvements over the previous version:
    - panZoom enabled so large diagrams (ER, flowcharts) are navigable
    - Font family matches the app; font size bumped for readability
    - Overflow scroll so diagrams never get clipped
    - Zoom controls (+/-/reset) overlaid on the diagram
    - White background with a subtle border
    """
    source = mermaid_source.strip()
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: Inter, "Segoe UI", system-ui, sans-serif;
    background: #fff; color: #0f172a;
    display: flex; flex-direction: column; height: 100%;
  }}
  .diag-title {{
    font-size: 13px; font-weight: 600; color: #334155;
    padding: 10px 14px 0; flex-shrink: 0;
  }}
  .diag-hint {{
    font-size: 11px; color: #94a3b8; padding: 3px 14px 8px;
    flex-shrink: 0;
  }}
  .diag-scroll {{
    flex: 1; overflow: auto; padding: 4px 14px 14px;
    display: flex; justify-content: center; align-items: flex-start;
  }}
  .mermaid {{
    width: 100%;
    max-width: none;
  }}
  .mermaid svg {{
    max-width: none !important;
    height: auto;
  }}
</style>
</head>
<body>
<div class="diag-title">{html.escape(title)}</div>
<div class="diag-hint">Scroll to navigate · click nodes to highlight</div>
<div class="diag-scroll">
  <pre class="mermaid">{source}</pre>
</div>
<script>
  mermaid.initialize({{
    startOnLoad: true,
    theme: "neutral",
    securityLevel: "loose",
    fontFamily: "Inter, Segoe UI, system-ui, sans-serif",
    fontSize: 14,
    er: {{ useMaxWidth: false, diagramPadding: 20 }},
    flowchart: {{ useMaxWidth: false, diagramPadding: 8 }},
  }});
</script>
</body>
</html>"""


def _legend_items() -> list[tuple[str, str, str]]:
    return [
        ("Product", "#1e40af", "Registered appliance knowledge"),
        ("Symptom", "#b45309", "Matched customer report"),
        ("Root cause", "#047857", "Ranked failure mode"),
        ("Part / fix", "#334155", "Recommended resolution"),
        ("Active path", "#047857", "Evidence chain for this diagnosis"),
    ]


def render_diagnosis_map_html(
    graph_data: dict[str, Any],
    diagnosis: dict[str, Any] | None = None,
    *,
    height: str = "480px",
    path_only: bool = True,
) -> str:
    """Premium diagnosis map: stepper timeline, legend, and hierarchical path graph."""
    filtered = filter_path_focus_graph(graph_data, path_only=path_only)
    prepared = prepare_executive_graph(filtered)
    net = _build_executive_pyvis_network(prepared, height=height)
    pyvis_raw = _sanitize_pyvis_html(net.generate_html(notebook=False))

    steps = diagnosis_map_steps(diagnosis)
    product = html.escape((diagnosis or {}).get("product_name") or (diagnosis or {}).get("product_id") or "Diagnosis")
    conf = (diagnosis or {}).get("confidence", 0)
    escalate = (diagnosis or {}).get("should_escalate", False)
    status_label = "Escalate" if escalate else "Resolved"
    status_class = "badge-warn" if escalate else "badge-ok"
    view_label = "Diagnosis path" if path_only else "Full context"

    stepper_html = ""
    for i, step in enumerate(steps):
        arrow = '<div class="dm-arrow">→</div>' if i < len(steps) - 1 else ""
        stepper_html += f"""
        <div class="dm-step">
          <div class="dm-step-num">{html.escape(step["stage"])}</div>
          <div class="dm-step-label">{html.escape(step["label"])}</div>
          <div class="dm-step-value">{html.escape(step["value"])}</div>
          <div class="dm-step-meta">{html.escape(step["meta"])}</div>
        </div>{arrow}"""

    legend_html = "".join(
        f'<span class="dm-legend-item"><i style="background:{color}"></i>'
        f"{html.escape(name)} <em>{html.escape(desc)}</em></span>"
        for name, color, desc in _legend_items()
    )

    node_count = prepared.get("node_count", len(prepared.get("nodes", [])))
    edge_count = prepared.get("edge_count", len(prepared.get("edges", [])))

    chrome = f"""
<div class="dm-shell">
  <div class="dm-header">
    <div>
      <div class="dm-title">Diagnosis reasoning map</div>
      <div class="dm-sub">{html.escape(view_label)} · {product}</div>
    </div>
    <div class="dm-badges">
      <span class="dm-badge badge-neutral">{conf:.0%} confidence</span>
      <span class="dm-badge {status_class}">{status_label}</span>
    </div>
  </div>
  <div class="dm-stepper">{stepper_html}</div>
  <div class="dm-legend">{legend_html}</div>
  <div class="dm-footer">
    <span>Drag to pan · scroll to zoom · green = evidence chain</span>
    <span>{node_count} concepts · {edge_count} relationships</span>
  </div>
</div>
<style>
  * {{ box-sizing: border-box; }}
  .dm-shell {{ border: 1px solid #e2e8f0; border-radius: 12px 12px 0 0; overflow: hidden; background: #fff; }}
  .dm-header {{ display: flex; justify-content: space-between; align-items: center; gap: 12px;
    padding: 14px 18px; background: linear-gradient(180deg, #f8fafc 0%, #fff 100%);
    border-bottom: 1px solid #e2e8f0; flex-wrap: wrap; }}
  .dm-title {{ font-size: 15px; font-weight: 600; }}
  .dm-sub {{ font-size: 12px; color: #64748b; margin-top: 2px; }}
  .dm-badges {{ display: flex; gap: 8px; flex-wrap: wrap; }}
  .dm-badge {{ font-size: 11px; font-weight: 600; padding: 4px 10px; border-radius: 999px; }}
  .badge-ok {{ background: #d1fae5; color: #065f46; }}
  .badge-warn {{ background: #fef3c7; color: #92400e; }}
  .badge-neutral {{ background: #e2e8f0; color: #334155; }}
  .dm-stepper {{ display: flex; align-items: stretch; padding: 14px 16px; overflow-x: auto;
    background: #f8fafc; border-bottom: 1px solid #e2e8f0; }}
  .dm-step {{ flex: 1; min-width: 130px; background: #fff; border: 1px solid #e2e8f0;
    border-radius: 10px; padding: 10px 12px; }}
  .dm-step-num {{ font-size: 10px; font-weight: 700; color: #047857; }}
  .dm-step-label {{ font-size: 10px; text-transform: uppercase; color: #64748b; }}
  .dm-step-value {{ font-size: 12px; font-weight: 600; margin-top: 4px; }}
  .dm-step-meta {{ font-size: 10px; color: #94a3b8; }}
  .dm-arrow {{ display: flex; align-items: center; padding: 0 4px; color: #94a3b8; }}
  .dm-legend {{ display: flex; flex-wrap: wrap; gap: 12px 18px; padding: 10px 18px;
    font-size: 11px; color: #475569; border-bottom: 1px solid #f1f5f9; }}
  .dm-legend-item {{ display: inline-flex; align-items: center; gap: 6px; }}
  .dm-legend-item i {{ width: 10px; height: 10px; border-radius: 3px; display: inline-block; }}
  .dm-footer {{ padding: 8px 18px; font-size: 11px; color: #94a3b8;
    border-top: 1px solid #f1f5f9; display: flex; justify-content: space-between; }}
  .graph-host {{ background: #fff; border: 1px solid #e2e8f0; border-top: none; border-radius: 0 0 12px 12px; }}
</style>"""
    return _compose_pyvis_shell(chrome, pyvis_raw)


def render_executive_graph_html(
    graph_data: dict[str, Any],
    *,
    height: str = "520px",
    title: str = "Diagnosis reasoning path",
    diagnosis: dict[str, Any] | None = None,
    path_only: bool = True,
) -> str:
    """Top-down hierarchical graph — delegates to the premium diagnosis map shell."""
    return render_diagnosis_map_html(
        graph_data,
        diagnosis,
        height=height,
        path_only=path_only,
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
    net.set_options(
        """
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
    """
        % ("true" if physics else "false")
    )

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

    return _sanitize_pyvis_html(net.generate_html(notebook=False))
