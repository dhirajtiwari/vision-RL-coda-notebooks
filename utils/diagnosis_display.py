"""
Executive-friendly diagnosis presentation: reasoning chains, grounding tables, traceability.

UI and formatting import from here — not from graph.provenance directly — to avoid
Streamlit module cache / circular import issues.
"""

from __future__ import annotations

from typing import Any

from graph.provenance import provenance_evidence_line


def format_traceability_lines(trail: list[dict[str, Any]], *, limit: int = 8) -> list[str]:
    lines: list[str] = []
    for pt in trail[:limit]:
        entity_type = pt.get("entity_type", "Entity")
        entity_id = pt.get("entity_id") or pt.get("source_record_id", "")
        enriched = provenance_evidence_line(entity_type, entity_id, pt)
        src = enriched.get("source_system", "Synthetic")
        record = enriched.get("source_record_id", entity_id)
        doc = enriched.get("source_document_uri") or record
        lines.append(f"- **{entity_type}** · {src} · `{record}` — {doc}")
    return lines


def enrich_provenance_trail(trail: list[dict]) -> list[dict]:
    return [
        provenance_evidence_line(
            e.get("entity_type", "Entity"),
            e.get("entity_id") or e.get("source_record_id", ""),
            e,
        )
        for e in trail
    ]


def grounding_records(diagnosis: dict[str, Any]) -> list[dict[str, str]]:
    """Tabular evidence grounding for executives and auditors."""
    rows: list[dict[str, str]] = []
    for pt in enrich_provenance_trail(diagnosis.get("provenance_trail") or []):
        rows.append(
            {
                "Evidence": pt.get("entity_type", ""),
                "Record ID": pt.get("entity_id") or pt.get("source_record_id", ""),
                "Source System": pt.get("source_system", ""),
                "Document / URI": pt.get("source_document_uri", "") or "—",
                "Approval": pt.get("approval_status", "") or "—",
            }
        )
    for ev in diagnosis.get("evidence") or []:
        if not any(ev in r.get("Record ID", "") for r in rows):
            rows.append(
                {
                    "Evidence": "Graph query",
                    "Record ID": "—",
                    "Source System": "Neo4j",
                    "Document / URI": ev[:120],
                    "Approval": "runtime",
                }
            )
    return rows


def reasoning_mermaid(diagnosis: dict[str, Any]) -> str:
    """Top-down reasoning chain for non-technical stakeholders."""
    product = (diagnosis.get("product_name") or diagnosis.get("product_id") or "Product").replace('"', "'")
    symptoms = diagnosis.get("matched_symptoms") or []
    top_fm = (diagnosis.get("ranked_failure_modes") or [None])[0] or {}
    fm_name = (top_fm.get("name") or "Unknown failure").replace('"', "'")
    conf = diagnosis.get("confidence", 0)
    parts = diagnosis.get("predicted_parts") or diagnosis.get("parts") or []
    part_name = (parts[0].get("name") if parts else "No part predicted").replace('"', "'")

    sym_nodes = []
    for i, s in enumerate(symptoms[:2]):
        desc = (s.get("description") or s.get("symptom_id", "symptom"))[:40].replace('"', "'")
        sym_nodes.append(f'    S{i}["Customer symptom: {desc}"]')

    lines = [
        "flowchart TB",
        f'    P["Product knowledge: {product}"]',
    ]
    lines.extend(sym_nodes)
    if sym_nodes:
        for i in range(len(sym_nodes)):
            lines.append(f"    P --> S{i}")
        if len(sym_nodes) > 1:
            lines.append(f"    {sym_nodes[0].split('[')[0].strip()} --> FM")
            lines.append(f"    {sym_nodes[1].split('[')[0].strip()} --> FM")
        else:
            lines.append("    S0 --> FM")
    else:
        lines.append("    P --> FM")
    lines.extend(
        [
            f'    FM["Diagnosis: {fm_name}<br/>Confidence {conf:.0%}"]',
            f'    PT["Recommended part: {part_name}"]',
            "    FM --> PT",
        ]
    )
    resolutions = diagnosis.get("historical_resolutions") or []
    if resolutions:
        res = (resolutions[0].get("description") or "")[:45].replace('"', "'")
        lines.append(f'    H["Prior field fix: {res}"]')
        lines.append("    FM --> H")
    return "\n".join(lines)


def knowledge_sources_summary(profile: dict[str, Any] | None) -> list[dict[str, str]]:
    if not profile:
        return []
    rows = []
    for src, count in (profile.get("source_counts") or {}).items():
        rows.append(
            {
                "Enterprise source": src,
                "Knowledge records": str(count),
                "Role": _source_role(src),
            }
        )
    return rows


def _source_role(source: str) -> str:
    return {
        "PIM": "Product catalog, symptoms, parts BOM",
        "FMEA": "Failure modes & reliability engineering",
        "ServiceManual": "Technician diagnostic procedures",
        "FSM": "Field service work orders & resolutions",
        "Claims": "Warranty claim precedents",
        "CRM": "Customer & asset registration (runtime)",
        "Synthetic": "Demo seed data",
    }.get(source, "Knowledge contributor")


def langgraph_workflow_mermaid() -> str:
    """Honest view of what LangGraph orchestrates in this demo."""
    return """flowchart LR
    A[Customer message] --> B[LangGraph: detect product]
    B --> C[LangGraph: GraphRAG diagnose]
    C --> D[LangGraph: format response]
    D --> E{Escalate?}
    E -->|Yes| F[Save case + CCaaS handoff]
    E -->|No| G[Automated answer]
    C -.-> H[(Neo4j knowledge graph)]
    H -.-> C"""


def platform_journey_mermaid() -> str:
    """End-to-end platform journey for the demo landing area."""
    return """flowchart TB
    subgraph inputs [What you provide]
      M[Customer symptom message]
      CRM[CRM asset optional]
    end
    subgraph orchestration [LangGraph workflow]
      LG[detect → diagnose → format → escalate]
    end
    subgraph intelligence [Neo4j GraphRAG — the reasoning engine]
      G1[Match symptoms]
      G2[Rank failure modes]
      G3[Parts + steps + provenance]
    end
    subgraph outputs [What you get]
      R[Explainable diagnosis]
      MAP[Reasoning map]
      AG[Agent dashboard if escalated]
    end
    M --> LG
    CRM --> LG
    LG --> G1 --> G2 --> G3
    G3 --> R
    G3 --> MAP
    LG --> AG"""


def architecture_faq_markdown() -> str:
    return """**Do we need LangGraph if we have Neo4j?**

Yes — they solve different problems. **Neo4j** is the knowledge brain (symptoms, failure modes, parts, lineage).
**LangGraph** is the workflow conductor: it runs the same steps in order every time (detect product → query graph →
format answer → escalate if needed). That gives you auditability, testability, and a place to add LLM rewrite,
human-in-the-loop, or extra enterprise calls later — without entangling UI code with graph logic.

**Is an LLM required?** No. This demo is graph-native: all diagnosis comes from Cypher + GraphRAG scoring.
LangGraph still adds value as orchestration scaffolding.

**What makes the answer trustworthy?** Every conclusion links to graph nodes with `source_system`, document URI,
and confidence on symptom→failure edges — shown in the Reasoning map and Evidence tabs."""


def executive_summary_markdown(
    diagnosis: dict[str, Any],
    *,
    user_prompt: str = "",
    crm_context: dict | None = None,
    warranty: dict | None = None,
    knowledge_profile: dict | None = None,
) -> str:
    product = diagnosis.get("product_name") or diagnosis.get("product_id") or "Unknown"
    top_fm = (diagnosis.get("ranked_failure_modes") or [None])[0] or {}
    fm_name = top_fm.get("name", "Under investigation")
    conf = diagnosis.get("confidence", 0)
    escalate = diagnosis.get("should_escalate", False)

    lines = [
        "### Diagnosis summary",
        f"**Customer report:** {user_prompt[:200] or '—'}",
        f"**Product:** {product}",
    ]
    if crm_context and crm_context.get("enriched"):
        lines.append(
            f"**Registered asset:** `{crm_context.get('asset_id', 'N/A')}` · "
            f"Customer: {crm_context.get('customer_name', 'N/A')}"
        )
    if warranty:
        lines.append(
            f"**Warranty:** {'Eligible' if warranty.get('eligible') else 'Review required'} — "
            f"{warranty.get('reason', '')}"
        )

    symptoms = diagnosis.get("matched_symptoms") or []
    if symptoms:
        lines.append("")
        lines.append("**Matched knowledge (symptoms from graph):**")
        for s in symptoms[:3]:
            lines.append(
                f"- {s.get('description')} _(match {s.get('match_score', 0):.0%}, "
                f"source: {s.get('source_system') or 'PIM'})_"
            )

    graph_conf = diagnosis.get("graph_confidence", 0)
    lang_conf = diagnosis.get("language_confidence", 0)
    lines.extend(
        [
            "",
            f"**Conclusion:** {fm_name} _(overall {conf:.0%} · graph {graph_conf:.0%} · language {lang_conf:.0%})_",
            f"**Action:** {'Escalate to human agent' if escalate else 'Automated resolution path'}",
        ]
    )
    if graph_conf and lang_conf and graph_conf > lang_conf + 0.25:
        lines.append(
            "> _Graph ontology strongly supports this diagnosis; language match is the limiting factor — "
            "the customer's words didn't align tightly with the catalog symptom phrase._"
        )
    if diagnosis.get("escalation_reason"):
        lines.append(f"**Escalation reason:** {diagnosis['escalation_reason']}")

    if knowledge_profile:
        lines.extend(
            [
                "",
                f"**Knowledge base for this product:** "
                f"{knowledge_profile.get('symptom_count', 0)} symptoms · "
                f"{knowledge_profile.get('failure_mode_count', 0)} failure modes · "
                f"{knowledge_profile.get('part_count', 0)} parts · "
                f"ETL batch `{knowledge_profile.get('etl_batch_id', 'n/a')}`",
            ]
        )

    for w in diagnosis.get("warnings") or []:
        lines.append(f"> ⚠️ {w}")

    return "\n".join(lines)
