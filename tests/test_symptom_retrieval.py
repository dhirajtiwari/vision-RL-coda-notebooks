"""Unit tests for hybrid symptom retrieval scoring."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from graph.symptom_retrieval import (  # noqa: E402
    build_idf,
    hybrid_symptom_score,
    tfidf_similarity,
)


def test_tfidf_similarity_paraphrase() -> None:
    query = "washer drum will not spin and water remains"
    doc = "washing machine won't spin and water stays in the drum"
    corpus = [doc, "dishwasher leaves dishes wet", "microwave food stays cold"]
    score = tfidf_similarity(query, doc, corpus)
    assert score > 0.2


def test_hybrid_boosts_agreeing_signals() -> None:
    message = "dishes come out wet and cold after the cycle"
    symptom = "Dishes come out wet and cold"
    lexical = 0.55
    score = hybrid_symptom_score(message, symptom, lexical_score=lexical)
    assert score >= lexical


def test_hybrid_penalizes_unrelated_symptom() -> None:
    message = "dishwasher leaves dishes wet and cold"
    symptom = "Microwave runs but food stays cold"
    lexical = 0.15
    score = hybrid_symptom_score(
        message,
        symptom,
        lexical_score=lexical,
        corpus=[symptom, "Dishes come out wet and cold"],
    )
    assert score < 0.35


def test_build_idf_nonempty() -> None:
    idf = build_idf(["washer spin drum", "dishwasher rinse cycle"])
    assert "washer" in idf or "spin" in idf
    assert all(v > 0 for v in idf.values())


if __name__ == "__main__":
    tests = [
        test_tfidf_similarity_paraphrase,
        test_hybrid_boosts_agreeing_signals,
        test_hybrid_penalizes_unrelated_symptom,
        test_build_idf_nonempty,
    ]
    failed = 0
    for test in tests:
        try:
            test()
            print(f"[PASS] {test.__name__}")
        except Exception as exc:
            failed += 1
            print(f"[FAIL] {test.__name__}: {exc}")
    raise SystemExit(1 if failed else 0)
