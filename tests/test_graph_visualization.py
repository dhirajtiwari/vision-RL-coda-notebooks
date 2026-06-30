"""Unit tests for graph visualization payloads."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from graph.graph_visualization import (
    diagnosis_subgraph_from_result,
    get_ontology_schema,
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


if __name__ == "__main__":
    test_ontology_schema_has_expected_labels()
    test_ontology_includes_requires_part_relationship()
    test_diagnosis_subgraph_from_result_empty_without_product()
    test_render_pyvis_html_produces_interactive_markup()
    print("PASS: graph visualization")