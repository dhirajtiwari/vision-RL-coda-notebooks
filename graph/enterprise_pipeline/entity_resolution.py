"""
Strong-node / weak-node entity resolution (industry KG-build practice).

Per the Scaling & Populating KG guide (Part 3, Step 4):

* **Strong nodes** come from a system of record (PIM / CRM / Claims / FSM /
  official catalog) — verified, high-confidence.
* **Weak nodes** come from unstructured / LLM extraction — plausible,
  schema-constrained, but unverified until resolved.
* A **resolution pass** merges a weak node into an existing strong node when
  they refer to the same real-world thing (e.g. "engine idles rough" →
  "rough idle"), instead of leaving confusing near-duplicates.

This module implements that pass with **stdlib only** (``difflib`` fuzzy string
similarity + token overlap) so it runs with no extra dependencies. Embedding
similarity is the [REFERENCE] upgrade (see ``docs/sdd/10-SCALING-POPULATING-KG.md``);
this deterministic resolver is the [AS-BUILT] baseline.

It produces *suggestions* — a review queue, never a silent merge — matching the
project rule "flag, don't silently fix or drop".
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Any

# Provenance / source markers that make a node "strong" (system of record).
STRONG_SOURCES = {"pim", "plm", "crm", "fsm", "claims", "catalog", "oem", "blueprint"}
# Markers that make a node "weak" (needs confirmation before it is trusted).
WEAK_SOURCES = {"unstructured", "llm", "provisional", "ticket", "manual", "transcript", "note"}

_DEFAULT_THRESHOLD = 0.82
_WORD_RE = re.compile(r"[a-z0-9]+")


def normalize(text: str) -> str:
    """Lowercase + collapse whitespace/punctuation for stable comparison."""
    return " ".join(_WORD_RE.findall((text or "").lower()))


def _stem(word: str) -> str:
    """Very light suffix stripping so 'idles'/'idling'/'idled' ~ 'idle'.

    Not a real stemmer — just enough to make inflection-only differences match
    without pulling in NLTK. Embedding similarity is the documented upgrade.
    """
    for suffix in ("ing", "ed", "es", "s"):
        if len(word) > len(suffix) + 2 and word.endswith(suffix):
            return word[: -len(suffix)]
    return word


def _tokens(text: str, *, stem: bool = False) -> set[str]:
    words = _WORD_RE.findall((text or "").lower())
    return {_stem(w) for w in words} if stem else set(words)


def similarity(a: str, b: str) -> float:
    """Blended fuzzy score in [0, 1] robust to re-ordering and inflection.

    Combines three signals without an embedding model:
    * raw sequence ratio,
    * **token-sort** ratio (sort words first → handles "rough idle" vs
      "idle rough"),
    * stemmed Jaccard token overlap (handles "idles"/"idling" vs "idle").
    Embedding similarity is the documented [REFERENCE] upgrade.
    """
    na, nb = normalize(a), normalize(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 1.0
    raw = SequenceMatcher(None, na, nb).ratio()
    sa = " ".join(sorted(na.split()))
    sb = " ".join(sorted(nb.split()))
    sort_ratio = SequenceMatcher(None, sa, sb).ratio()
    ta, tb = _tokens(a, stem=True), _tokens(b, stem=True)
    jac = len(ta & tb) / len(ta | tb) if (ta | tb) else 0.0
    return round(max(raw, sort_ratio, 0.5 * sort_ratio + 0.5 * jac), 4)


def classify_strength(source: str | None, provenance: dict[str, Any] | None = None) -> str:
    """Return 'strong' | 'weak' | 'unknown' from a source tag / provenance dict."""
    hay = (source or "").lower()
    if provenance:
        hay += " " + " ".join(str(v).lower() for v in provenance.values())
    if any(tok in hay for tok in STRONG_SOURCES):
        return "strong"
    if any(tok in hay for tok in WEAK_SOURCES):
        return "weak"
    return "unknown"


@dataclass
class ResolutionSuggestion:
    weak_id: str
    weak_text: str
    strong_id: str
    strong_text: str
    score: float
    action: str  # "merge" (>= threshold) | "review" (borderline)

    def as_dict(self) -> dict[str, Any]:
        return {
            "weak_id": self.weak_id,
            "weak_text": self.weak_text,
            "strong_id": self.strong_id,
            "strong_text": self.strong_text,
            "score": self.score,
            "action": self.action,
        }


@dataclass
class ResolutionReport:
    suggestions: list[ResolutionSuggestion] = field(default_factory=list)
    unmatched_weak: list[str] = field(default_factory=list)

    @property
    def merge_count(self) -> int:
        return sum(1 for s in self.suggestions if s.action == "merge")

    def as_dict(self) -> dict[str, Any]:
        return {
            "merge_count": self.merge_count,
            "review_count": len(self.suggestions) - self.merge_count,
            "unmatched_weak": self.unmatched_weak,
            "suggestions": [s.as_dict() for s in self.suggestions],
        }


def resolve_weak_to_strong(
    weak_nodes: list[dict[str, Any]],
    strong_nodes: list[dict[str, Any]],
    *,
    id_field: str,
    text_field: str,
    threshold: float = _DEFAULT_THRESHOLD,
    review_band: float = 0.10,
) -> ResolutionReport:
    """Match each weak node to its best strong node by fuzzy text similarity.

    * score >= ``threshold``                → action="merge" (same real-world thing)
    * ``threshold - review_band`` <= score  → action="review" (borderline, human)
    * below that                            → unmatched (a genuinely new node)
    """
    report = ResolutionReport()
    for weak in weak_nodes:
        w_id = str(weak.get(id_field, ""))
        w_text = str(weak.get(text_field, ""))
        best: tuple[float, dict[str, Any]] | None = None
        for strong in strong_nodes:
            score = similarity(w_text, str(strong.get(text_field, "")))
            if best is None or score > best[0]:
                best = (score, strong)
        if best is None or best[0] < (threshold - review_band):
            report.unmatched_weak.append(w_id)
            continue
        s_node = best[1]
        report.suggestions.append(
            ResolutionSuggestion(
                weak_id=w_id,
                weak_text=w_text,
                strong_id=str(s_node.get(id_field, "")),
                strong_text=str(s_node.get(text_field, "")),
                score=best[0],
                action="merge" if best[0] >= threshold else "review",
            )
        )
    return report


def find_near_duplicates(
    nodes: list[dict[str, Any]],
    *,
    id_field: str,
    text_field: str,
    threshold: float = _DEFAULT_THRESHOLD,
) -> list[dict[str, Any]]:
    """Flag near-duplicate nodes *within one pool* (e.g. two similar symptoms).

    Returns a list of ``{a_id, b_id, score}`` for pairs at or above ``threshold``
    — a review queue, not an auto-merge.
    """
    dups: list[dict[str, Any]] = []
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            a, b = nodes[i], nodes[j]
            score = similarity(str(a.get(text_field, "")), str(b.get(text_field, "")))
            if score >= threshold:
                dups.append(
                    {
                        "a_id": str(a.get(id_field, "")),
                        "b_id": str(b.get(id_field, "")),
                        "score": score,
                    }
                )
    return dups
