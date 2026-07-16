"""Tests for the schema-bound LLM extractor (no live API call).

Exercises the ontology binding, allow-list filtering, and the disabled default —
never hits OpenAI, so it is safe and free in CI.
"""

from __future__ import annotations

from graph.enterprise_pipeline.extractors import llm_graph_extract as lge


def test_allowed_nodes_and_relationships_from_tbox():
    nodes = lge.allowed_nodes()
    rels = lge.allowed_relationships()
    # Core ontology classes/relationships must be present and be plain strings.
    assert "Symptom" in nodes and "FailureMode" in nodes and "Part" in nodes
    assert "INDICATES" in rels and "REQUIRES_PART" in rels
    assert all(isinstance(x, str) for x in nodes + rels)


def test_disabled_by_default(monkeypatch):
    monkeypatch.setattr(lge.settings, "llm_enabled", False, raising=False)
    ok, reason = lge.is_available()
    assert ok is False
    r = lge.extract_graph_from_text("washer wont spin", doc_id="t")
    assert r["enabled"] is False
    assert r["method"] == "disabled"
    assert r["nodes"] == [] and r["relationships"] == []


def test_missing_key_reported(monkeypatch):
    monkeypatch.setattr(lge.settings, "llm_enabled", True, raising=False)
    monkeypatch.setattr(lge.settings, "openai_api_key", None, raising=False)
    ok, reason = lge.is_available()
    assert ok is False
    assert "OPENAI_API_KEY" in reason


def test_extraction_schema_enumerates_ontology():
    a_nodes, a_rels = lge.allowed_nodes(), lge.allowed_relationships()
    schema = lge._extraction_schema(a_nodes, a_rels)
    assert schema["properties"]["nodes"]["items"]["properties"]["type"]["enum"] == a_nodes
    assert schema["properties"]["relationships"]["items"]["properties"]["type"]["enum"] == a_rels


def test_filter_drops_out_of_allowlist():
    a_nodes = ["Symptom", "Part"]
    a_rels = ["INDICATES"]
    result = {
        "nodes": [
            {"id": "rough idle", "type": "Symptom"},
            {"id": "hallucinated", "type": "NotAClass"},  # dropped
            {"id": "", "type": "Part"},  # dropped (no id)
        ],
        "relationships": [
            {"source": "a", "target": "b", "type": "INDICATES"},
            {"source": "a", "target": "b", "type": "INVENTED_REL"},  # dropped
        ],
    }
    nodes, rels = lge._filter_to_ontology(result, a_nodes, a_rels)
    assert [n["id"] for n in nodes] == ["rough idle"]
    assert all(n["source"] == "llm" for n in nodes)
    assert [r["type"] for r in rels] == ["INDICATES"]
