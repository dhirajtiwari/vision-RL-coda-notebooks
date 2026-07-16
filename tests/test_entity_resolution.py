"""Tests for the strong/weak entity resolver (stdlib, no Neo4j required)."""

from __future__ import annotations

from graph.enterprise_pipeline.entity_resolution import (
    classify_strength,
    find_near_duplicates,
    resolve_weak_to_strong,
    similarity,
)


def test_similarity_identical_and_reorder():
    assert similarity("rough idle", "rough idle") == 1.0
    # word reorder should still score high
    assert similarity("rough idle", "idle rough") >= 0.8


def test_similarity_inflection_stem():
    # 'idling'/'idles' stem to 'idl' so these near-match
    assert similarity("rough idling", "rough idle") >= 0.7
    assert similarity("drain pump failure", "drain pump failed") >= 0.7


def test_similarity_unrelated_low():
    # Unrelated phrases must stay well below the merge threshold (0.82).
    assert similarity("water leak under door", "no power to unit") < 0.6


def test_classify_strength():
    assert classify_strength("pim_catalog") == "strong"
    assert classify_strength("crm") == "strong"
    assert classify_strength("llm_extraction") == "weak"
    assert classify_strength("unstructured_extract") == "weak"
    assert classify_strength("something_else") == "unknown"
    # provenance dict is also inspected
    assert classify_strength(None, {"source_system": "FSM"}) == "strong"


def test_resolve_weak_to_strong_merge_and_unmatched():
    weak = [
        {"symptom_id": "w1", "description": "rough idling"},
        {"symptom_id": "w2", "description": "completely unrelated observation xyz"},
    ]
    strong = [
        {"symptom_id": "s1", "description": "rough idle"},
        {"symptom_id": "s2", "description": "no power"},
    ]
    report = resolve_weak_to_strong(weak, strong, id_field="symptom_id", text_field="description")
    d = report.as_dict()
    # w1 should map to s1
    mapped = {s["weak_id"]: s["strong_id"] for s in d["suggestions"]}
    assert mapped.get("w1") == "s1"
    # w2 has no strong match
    assert "w2" in d["unmatched_weak"]


def test_find_near_duplicates_within_pool():
    nodes = [
        {"symptom_id": "a", "description": "drain pump failure"},
        {"symptom_id": "b", "description": "drain pump failed"},
        {"symptom_id": "c", "description": "door latch broken"},
    ]
    dups = find_near_duplicates(nodes, id_field="symptom_id", text_field="description")
    pairs = {(d["a_id"], d["b_id"]) for d in dups}
    assert ("a", "b") in pairs
    assert all("c" not in p for p in pairs)
