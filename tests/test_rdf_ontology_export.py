"""Tests for RDF/OWL ontology export (stdlib, no Neo4j required)."""

from __future__ import annotations

from pathlib import Path

from graph.rdf_ontology_export import (
    catalog_to_turtle,
    export_ontology,
    schema_only_turtle,
    schema_to_rdfxml,
)

MINI_CATALOG = {
    "products": [
        {
            "product": {
                "product_id": "wm-001",
                "name": "AquaHome Front Load 8kg",
                "category": "Washing Machine",
                "brand": "AquaHome",
            },
            "symptoms": [
                {
                    "symptom_id": "wm-s03",
                    "description": "Will not drain",
                    "severity": "high",
                }
            ],
            "failure_modes": [
                {
                    "failure_mode_id": "wm-fm02",
                    "name": "Drain pump failure",
                    "description": "Pump seized or blocked",
                }
            ],
            "symptom_failure_links": [{"symptom_id": "wm-s03", "failure_mode_id": "wm-fm02", "confidence": 0.91}],
            "components": [
                {
                    "component_id": "wm-c02",
                    "name": "Drain System",
                    "subsystem": "Plumbing",
                }
            ],
            "parts": [
                {
                    "part_id": "wm-p02",
                    "name": "Drain pump",
                    "part_number": "DP-8K-01",
                    "estimated_cost_usd": 89.0,
                }
            ],
            "failure_mode_component_links": [
                {
                    "failure_mode_id": "wm-fm02",
                    "component_id": "wm-c02",
                    "impact_severity": "primary",
                }
            ],
            "component_part_links": [{"component_id": "wm-c02", "part_id": "wm-p02"}],
            "failure_mode_part_links": [
                {
                    "failure_mode_id": "wm-fm02",
                    "part_id": "wm-p02",
                    "quantity": 1,
                    "probability": 0.91,
                    "is_primary": True,
                }
            ],
            "diagnostic_steps": [],
            "skus": [],
            "error_codes": [],
        }
    ],
    "assets": [],
    "warranty_policies": [],
    "claims": [],
}


def test_schema_only_turtle_has_owl_classes():
    ttl = schema_only_turtle()
    assert "owl:Ontology" in ttl
    assert "wd:Product" in ttl
    assert "wd:FailureMode" in ttl
    assert "wd:impactsComponent" in ttl
    assert "wd:realizedBy" in ttl


def test_catalog_to_turtle_includes_abox_chain():
    ttl = catalog_to_turtle(MINI_CATALOG, product_ids=["wm-001"])
    assert "wd:product_wm-001" in ttl
    assert "wd:symptom_wm-s03" in ttl
    assert "wd:indicates" in ttl
    assert "wd:impactsComponent" in ttl
    assert "wd:realizedBy" in ttl
    assert "wd:requiresPart" in ttl


def test_schema_rdfxml_is_well_formed_xml_fragment():
    rdf = schema_to_rdfxml()
    assert rdf.startswith("<?xml")
    assert "owl:Class" in rdf
    assert "wd:Product" in rdf
    assert "</rdf:RDF>" in rdf


def test_export_ontology_writes_file(tmp_path: Path):
    out = tmp_path / "demo.ttl"
    # schema-only path does not need a real catalog file
    path = export_ontology(out_path=out, fmt="turtle", schema_only=True)
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "@prefix wd:" in text
    assert "owl:Class" in text or "a owl:Class" in text
