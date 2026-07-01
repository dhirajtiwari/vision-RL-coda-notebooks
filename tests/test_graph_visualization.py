"""Unit tests for graph visualization payloads."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from graph.graph_visualization import (
    diagnosis_map_steps,
    diagnosis_subgraph_from_result,
    filter_path_focus_graph,
    get_ontology_schema,
    ontology_mermaid_diagram,
    product_graph_summary,
    render_diagnosis_map_html,
    render_pyvis_html,
)


def test_ontology_schema_has_expected_labels():
    data = get_ontology_schema()
    labels = {n["entity_id"] for n in data["nodes"]}
    assert "Product" in labels
    assert "Symptom" in labels
    assert "FailureMode" in labels
    assert "Part" in labels
    assert data["edge_count"] >= 6


def test_ontology_includes_requires_part_relationship():
    data = get_ontology_schema()
    rel_types = {e["type"] for e in data["edges"]}
    assert "REQUIRES_PART {confidence}" not in rel_types
    assert any("REQUIRES_PART" in t for t in rel_types)


def test_diagnosis_subgraph_from_result_empty_without_product():
    data = diagnosis_subgraph_from_result({})
    assert data["node_count"] == 0


def test_render_pyvis_html_produces_interactive_markup():
    data = get_ontology_schema()
    html = render_pyvis_html(data, height="400px", physics=False)
    assert "vis-network" in html or "network" in html.lower()
    assert "Product" in html


def test_filter_path_focus_reduces_noise():
    data = {
        "nodes": [
            {"id": "Product:p1", "label": "Product", "highlight": True},
            {"id": "Symptom:s1", "label": "Symptom", "highlight": True},
            {"id": "DiagnosticStep:d1", "label": "DiagnosticStep", "highlight": False},
        ],
        "edges": [
            {"source": "Product:p1", "target": "Symptom:s1", "type": "HAS_SYMPTOM", "highlight": True},
            {"source": "Product:p1", "target": "DiagnosticStep:d1", "type": "HAS_DIAGNOSTIC_STEP", "highlight": False},
        ],
        "node_count": 3,
        "edge_count": 2,
    }
    focused = filter_path_focus_graph(data, path_only=True)
    assert focused["node_count"] == 2
    assert focused["edge_count"] == 1


def test_diagnosis_map_steps_from_payload():
    steps = diagnosis_map_steps({
        "product_name": "CleanWave Dishwasher",
        "matched_symptoms": [{"description": "Dishes wet", "match_score": 0.6}],
        "ranked_failure_modes": [{"name": "Heating Element Failure"}],
        "confidence": 0.72,
        "parts": [{"name": "Heating Element", "part_number": "DW-HE-001"}],
    })
    assert len(steps) >= 4
    assert steps[0]["label"] == "Product"


def test_ontology_mermaid_contains_core_entities():
    diagram = ontology_mermaid_diagram()
    assert "Product" in diagram
    assert "Symptom" in diagram
    assert "FailureMode" in diagram


def test_product_graph_summary_counts_labels():
    data = {
        "nodes": [
            {"label": "Product"},
            {"label": "Symptom"},
            {"label": "Symptom"},
        ],
        "edges": [],
    }
    assert product_graph_summary(data)["Symptom"] == 2


def test_render_diagnosis_map_html_includes_stepper_and_graph():
    data = {
        "nodes": [
            {"id": "Product:dw-001", "label": "Product", "entity_id": "dw-001",
             "title": "CleanWave", "highlight": True, "layer": 0},
            {"id": "Symptom:dw-s01", "label": "Symptom", "entity_id": "dw-s01",
             "title": "Dishes wet", "highlight": True, "layer": 1},
        ],
        "edges": [
            {"source": "Product:dw-001", "target": "Symptom:dw-s01",
             "type": "HAS_SYMPTOM", "highlight": True},
        ],
        "node_count": 2,
        "edge_count": 1,
    }
    prepared = __import__("graph.graph_visualization", fromlist=["prepare_executive_graph"]).prepare_executive_graph(data)
    for node in prepared["nodes"]:
        node["executive_label"] = node.get("title", node["entity_id"])
    html = render_diagnosis_map_html(
        data,
        {"product_name": "CleanWave", "confidence": 0.6, "matched_symptoms": [{"description": "Dishes wet", "match_score": 0.6}]},
        height="320px",
    )
    assert "Diagnosis reasoning map" in html
    assert "dm-stepper" in html
    assert "dm-legend" in html
    assert "vis-network.min.js" in html


if __name__ == "__main__":
    test_ontology_schema_has_expected_labels()
    test_ontology_includes_requires_part_relationship()
    test_diagnosis_subgraph_from_result_empty_without_product()
    test_render_pyvis_html_produces_interactive_markup()
    test_filter_path_focus_reduces_noise()
    test_diagnosis_map_steps_from_payload()
    test_ontology_mermaid_contains_core_entities()
    test_product_graph_summary_counts_labels()
    test_render_diagnosis_map_html_includes_stepper_and_graph()
    print("PASS: graph visualization")