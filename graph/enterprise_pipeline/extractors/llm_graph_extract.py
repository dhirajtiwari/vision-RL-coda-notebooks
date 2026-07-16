"""
Schema-bound LLM extraction of graph triples from unstructured text.

Industry practice (Scaling & Populating KG guide, Part 3, Step 3): when you use
an LLM to turn manuals / tickets / transcripts into graph data, you must
**bind it to your ontology** — allow only your classes and relationships — so it
can never invent a type. Free-form extraction on smaller models produces "an
unusable, inconsistent mess".

Posture in this project:

* **Default OFF** — gated on ``settings.llm_enabled`` (False by default). Core
  diagnosis is deterministic GraphRAG; this is an *optional* enrichment path.
* **Cheapest model** — ``settings.llm_extract_model`` (default ``gpt-4o-mini``).
  Extraction is a bulk/offline job, so it uses the cheap model on purpose.
* **Key from env only** — the OpenAI key is read from ``settings.openai_api_key``
  (env ``OPENAI_API_KEY``); it is never hard-coded or written to disk.
* **Ontology-bound two ways** — (1) the LLM is asked for **structured output**
  whose schema enumerates only the TBox classes/relationships, and (2) the code
  drops anything outside the allow-lists (defense in depth). So the model can
  only ever yield ontology-legal triples.
* **Fail-open to deterministic** — if disabled or ``langchain-openai`` is
  missing, callers fall back to ``unstructured_text.extract_from_text`` (regex).

Output nodes are **weak nodes** (see ``entity_resolution``) until a resolution
pass merges them into strong catalog nodes and shape validation passes.
"""

from __future__ import annotations

from typing import Any

from config.settings import settings
from graph.rdf_ontology_export import CLASSES, OBJECT_PROPERTIES

# gpt-4o-mini list price (USD per 1K tokens) — used to meter estimated spend.
# Approximate for other models; extraction is a cheap bulk job, not the hot path.
_PRICE_IN_PER_1K = 0.00015
_PRICE_OUT_PER_1K = 0.0006


def allowed_nodes() -> list[str]:
    """TBox class names the LLM is allowed to emit (schema binding)."""
    return [name for name, _comment in CLASSES]


def allowed_relationships() -> list[str]:
    """TBox object-property Neo4j relationship types the LLM may emit."""
    rels: list[str] = []
    for entry in OBJECT_PROPERTIES:
        # OBJECT_PROPERTIES rows are (name, domain, range, comment, neo4j_type)
        neo = entry[-1] if len(entry) >= 5 else entry[0]
        if neo and neo not in rels:
            rels.append(str(neo))
    return rels


def is_available() -> tuple[bool, str]:
    """Return (enabled_and_importable, reason)."""
    if not settings.llm_enabled:
        return False, "llm_enabled=false (deterministic GraphRAG is primary)"
    if not settings.openai_api_key:
        return False, "OPENAI_API_KEY not set (inject via env, never commit)"
    try:  # optional dep — only imported when explicitly enabled
        import langchain_openai  # noqa: F401
    except Exception as exc:  # pragma: no cover - import guard
        return False, f"langchain-openai not installed: {exc}"
    return True, "ready"


def _build_cheap_chat_model():
    """Construct the cheapest ChatOpenAI from settings (key read from env)."""
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=settings.llm_extract_model,
        temperature=0,
        api_key=settings.openai_api_key,
        max_retries=2,
        timeout=30,
    )


def _extraction_schema(a_nodes: list[str], a_rels: list[str]) -> dict[str, Any]:
    """JSON schema that constrains the LLM output to the ontology."""
    return {
        "title": "OntologyGraphExtraction",
        "description": "Graph triples extracted from text, bound to the TBox.",
        "type": "object",
        "properties": {
            "nodes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "description": "short natural id / name"},
                        "type": {"type": "string", "enum": a_nodes},
                    },
                    "required": ["id", "type"],
                },
            },
            "relationships": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "source": {"type": "string"},
                        "target": {"type": "string"},
                        "type": {"type": "string", "enum": a_rels},
                    },
                    "required": ["source", "target", "type"],
                },
            },
        },
        "required": ["nodes", "relationships"],
    }


def _meter_usage(raw: Any, budget: Any) -> dict[str, Any]:
    """Estimate token cost from the raw AIMessage and record it on the budget."""
    try:
        msg = raw.get("raw") if isinstance(raw, dict) else None
        um = getattr(msg, "usage_metadata", None) or {}
        in_tok, out_tok = int(um.get("input_tokens", 0)), int(um.get("output_tokens", 0))
        cost_usd = round(in_tok / 1000 * _PRICE_IN_PER_1K + out_tok / 1000 * _PRICE_OUT_PER_1K, 6)
        budget.record(cost_usd)
        return {"input_tokens": in_tok, "output_tokens": out_tok, "estimated_cost_usd": cost_usd}
    except Exception:  # pragma: no cover - metering must never break extraction
        return {}


def _filter_to_ontology(
    result: dict[str, Any], a_nodes: list[str], a_rels: list[str]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Defense in depth: drop anything the model emitted outside the allow-lists."""
    node_set, nodes = set(a_nodes), []
    for n in result.get("nodes", []) or []:
        if n.get("type") in node_set and n.get("id"):
            nodes.append({"id": str(n["id"]), "type": str(n["type"]), "source": "llm", "confidence": 0.5})
    rel_set, relationships = set(a_rels), []
    for r in result.get("relationships", []) or []:
        if r.get("type") in rel_set and r.get("source") and r.get("target"):
            relationships.append({"source": str(r["source"]), "target": str(r["target"]), "type": str(r["type"])})
    return nodes, relationships


def extract_graph_from_text(
    text: str,
    *,
    doc_id: str = "",
    llm: Any | None = None,
) -> dict[str, Any]:
    """Extract ontology-bound (nodes, relationships) from free text via an LLM.

    Returns a dict with ``enabled``, ``method``, ``nodes``, ``relationships`` and
    ``allowed_*``. When disabled/unavailable, ``enabled`` is False and callers
    should fall back to the deterministic extractor — nodes/relationships empty.
    """
    a_nodes = allowed_nodes()
    a_rels = allowed_relationships()
    ok, reason = is_available()
    if not ok:
        return {
            "enabled": False,
            "method": "disabled",
            "reason": reason,
            "doc_id": doc_id,
            "allowed_nodes": a_nodes,
            "allowed_relationships": a_rels,
            "nodes": [],
            "relationships": [],
            "note": "fall back to unstructured_text.extract_from_text (regex).",
        }

    # LLM path (only reached when llm_enabled=true AND langchain-openai present).
    model = llm or _build_cheap_chat_model()

    # FinOps: check the daily budget BEFORE spending; fail closed if the circuit
    # is open (never silently exceed the cap). Record realised spend after.
    from finops.budget import BudgetExceeded, DailyCostBudget

    budget = DailyCostBudget.from_settings()
    try:
        budget.check()
    except BudgetExceeded as exc:
        return {
            "enabled": False,
            "method": "budget_exceeded",
            "reason": str(exc),
            "doc_id": doc_id,
            "allowed_nodes": a_nodes,
            "allowed_relationships": a_rels,
            "nodes": [],
            "relationships": [],
            "note": "daily LLM budget reached — fall back to deterministic extraction.",
        }

    structured = model.with_structured_output(_extraction_schema(a_nodes, a_rels), include_raw=True)
    prompt = (
        "Extract a knowledge graph from the diagnostic text below. You may ONLY "
        f"use these node types: {a_nodes}. You may ONLY use these relationship "
        f"types: {a_rels}. Do not invent types. Prefer few, high-confidence "
        "triples over many speculative ones.\n\nTEXT:\n" + text
    )
    raw = structured.invoke(prompt)
    result = (raw.get("parsed") if isinstance(raw, dict) else raw) or {}
    usage = _meter_usage(raw, budget)
    nodes, relationships = _filter_to_ontology(result, a_nodes, a_rels)
    return {
        "enabled": True,
        "method": f"chatopenai:{settings.llm_extract_model}",
        "doc_id": doc_id,
        "allowed_nodes": a_nodes,
        "allowed_relationships": a_rels,
        "nodes": nodes,
        "relationships": relationships,
        "usage": usage,
        "budget_backend": budget.backend,
        "note": "weak nodes — resolve to strong catalog nodes + shape-validate before promote.",
    }
