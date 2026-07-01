"""
Enterprise Diagnostics Chatbot Demo — Streamlit UI

Run: streamlit run ui/app.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
import streamlit.components.v1 as components

from config.settings import settings
from graph.graph_rag import detect_product, list_products
from ui.theme import inject_theme
from utils.diagnosis_display import (
    architecture_faq_markdown,
    enrich_provenance_trail,
    executive_summary_markdown,
    format_traceability_lines,
    grounding_records,
    knowledge_sources_summary,
    langgraph_workflow_mermaid,
    platform_journey_mermaid,
    reasoning_mermaid,
)
from graph.neo4j_client import verify_connection
from integrations.crm_enrichment import enrich_session_from_crm
from integrations.warranty_eligibility import check_warranty_eligibility
from integrations.claims_workflow import list_submitted_claims, submit_claim_from_diagnosis, update_claim_status
from services.diagnosis_service import run_full_diagnosis
from utils.connector_status import integration_status
from utils.escalation_store import count_escalations, list_escalations, update_escalation_status
from utils.lineage_store import list_batches
from utils.persistence import get_store

st.set_page_config(
    page_title="Diagnostics Chatbot Demo",
    page_icon="🔧",
    layout="wide",
)

PAGES = (
    "💬 Chat",
    "📋 Claims",
    "👤 Agents",
    "🕸️ Knowledge Graph",
    "🏢 Enterprise",
)

PAGE_HELP = {
    PAGES[0]: "Describe a symptom → get an explainable diagnosis with reasoning map.",
    PAGES[1]: "Warranty claims submitted from diagnosed cases.",
    PAGES[2]: "Human review queue for escalated low-confidence or critical cases.",
    PAGES[3]: "Explore ontology, product knowledge, and diagnosis paths in Neo4j.",
    PAGES[4]: "ETL lineage, connector health, and simulated case handoffs.",
}

CRM_FIXTURES = settings.enterprise_sources_dir / "crm_assets.json"


# ── Cached loaders (avoid Neo4j/HTTP on every widget click) ───────────────────

@st.cache_data(ttl=30, show_spinner=False)
def _cached_neo4j_ok() -> bool:
    return verify_connection()


@st.cache_data(ttl=30, show_spinner=False)
def _cached_mock_ok() -> bool:
    try:
        from graph.enterprise_pipeline.http_client import get_json

        get_json(f"{settings.mock_enterprise_api_url.rstrip('/')}/health")
        return True
    except ConnectionError:
        return False


@st.cache_data(ttl=120, show_spinner=False)
def _cached_crm_fixtures() -> dict:
    if CRM_FIXTURES.exists():
        return json.loads(CRM_FIXTURES.read_text(encoding="utf-8"))
    return {"customers": [], "registered_assets": []}


@st.cache_data(ttl=60, show_spinner=False)
def _cached_products() -> list[dict]:
    return list_products()


@st.cache_data(ttl=300, show_spinner=False)
def _cached_executive_graph_html(
    graph_json: str,
    height: int,
    diagnosis_json: str,
    path_only: bool,
) -> str:
    from graph.graph_visualization import render_executive_graph_html

    graph_data = json.loads(graph_json)
    diagnosis = json.loads(diagnosis_json) if diagnosis_json else None
    return render_executive_graph_html(
        graph_data,
        diagnosis=diagnosis,
        height=f"{height}px",
        path_only=path_only,
    )


@st.cache_data(ttl=300, show_spinner=False)
def _cached_pyvis_html(graph_json: str, height: int, physics: bool) -> str:
    from graph.graph_visualization import render_pyvis_html

    graph_data = json.loads(graph_json)
    return render_pyvis_html(graph_data, height=f"{height}px", physics=physics)


@st.cache_data(ttl=600, show_spinner=False)
def _cached_mermaid_html(mermaid_source: str, title: str) -> str:
    from graph.graph_visualization import render_mermaid_html

    return render_mermaid_html(mermaid_source, title=title)


@st.cache_data(ttl=120, show_spinner=False)
def _cached_ontology_schema() -> dict:
    from graph.graph_visualization import get_ontology_schema

    return get_ontology_schema()


@st.cache_data(ttl=120, show_spinner=False)
def _cached_product_subgraph(product_id: str) -> dict:
    from graph.graph_visualization import get_product_subgraph

    return get_product_subgraph(product_id)


@st.cache_data(ttl=60, show_spinner=False)
def _cached_open_escalations() -> int:
    return count_escalations(status="open")


@st.cache_data(ttl=60, show_spinner=False)
def _cached_product_knowledge_html(graph_json: str, product_name: str, height: int) -> str:
    from graph.graph_visualization import render_product_knowledge_html

    return render_product_knowledge_html(json.loads(graph_json), product_name=product_name, height=f"{height}px")


@st.cache_data(ttl=120, show_spinner=False)
def _cached_diagnosis_subgraph(product_id: str, symptom_ids_key: str, failure_mode_id: str) -> dict:
    from graph.graph_visualization import get_diagnosis_subgraph

    symptom_ids = symptom_ids_key.split(",") if symptom_ids_key else []
    return get_diagnosis_subgraph(product_id, symptom_ids=symptom_ids, failure_mode_id=failure_mode_id or None)


def _graph_cache_key(graph_data: dict) -> str:
    payload = json.dumps(graph_data, sort_keys=True, default=str)
    return hashlib.md5(payload.encode()).hexdigest()[:12]


def _load_simulated_cases() -> list[dict]:
    return get_store().list_cases()


def _batch_status_icon(status: str) -> str:
    return {
        "success": "✅",
        "failed": "❌",
        "dry_run": "📋",
        "blocked": "🚫",
        "partial": "⚠️",
    }.get(status, "⏳")


def _format_batch_source(name: str, src: object) -> str:
    if isinstance(src, dict):
        if "record_count" in src or "mode" in src:
            return f"{src.get('record_count', 0)} records ({src.get('mode', 'unknown')})"
        if "ok" in src:
            state = "OK" if src.get("ok") else "FAIL"
            return f"{state} — {src.get('record_count', 0)} records ({src.get('mode', 'unknown')})"
        return json.dumps(src)
    return str(src)


def _render_executive_reasoning_graph(
    graph_data: dict | None,
    *,
    graph_key: str,
    diagnosis: dict | None = None,
    height: int = 560,
) -> None:
    """Premium diagnosis reasoning map with stepper, legend, and path-focused graph."""
    if not graph_data or not graph_data.get("nodes"):
        st.caption("No reasoning graph available.")
        return

    path_only = st.toggle(
        "Focus on diagnosis path only",
        value=True,
        key=f"path_focus_{graph_key}",
        help="Shows only the evidence chain for this answer. Turn off to include adjacent graph context.",
    )

    with st.spinner("Building reasoning map…"):
        html = _cached_executive_graph_html(
            json.dumps(graph_data, sort_keys=True, default=str),
            height,
            json.dumps(diagnosis or {}, sort_keys=True, default=str),
            path_only,
        )
    components.html(html, height=height + 220, scrolling=True)


def _render_diagnosis_explainability(
    diagnosis: dict,
    *,
    user_prompt: str = "",
    crm_context: dict | None = None,
    warranty: dict | None = None,
    graph_key: str = "diag",
    show_graph: bool = True,
) -> None:
    """Executive briefing: summary, reasoning map, evidence, and technical detail."""
    profile = diagnosis.get("knowledge_profile")
    subgraph = diagnosis.get("graph_subgraph")

    st.markdown(
        executive_summary_markdown(
            diagnosis,
            user_prompt=user_prompt,
            crm_context=crm_context,
            warranty=warranty,
            knowledge_profile=profile,
        )
    )

    tab_map, tab_evidence, tab_technical = st.tabs(
        ["🗺️ Reasoning map", "📎 Evidence", "⚙️ Technical"]
    )

    with tab_map:
        if subgraph and show_graph:
            _render_executive_reasoning_graph(
                subgraph,
                graph_key=graph_key,
                diagnosis=diagnosis,
            )
        elif subgraph:
            st.caption("Open **Show reasoning map** above to render the interactive diagram.")
        else:
            st.info("Graph reasoning path will appear after the next diagnosis query.")
            st.markdown(f"```mermaid\n{reasoning_mermaid(diagnosis)}\n```")

    with tab_evidence:
        ground = grounding_records(diagnosis)
        if ground:
            st.markdown("**Evidence grounding (audit trail)**")
            st.dataframe(ground, use_container_width=True, hide_index=True)
        else:
            st.caption("No provenance trail attached to this diagnosis.")

        st.markdown("**Knowledge built from (enterprise sources)**")
        src_rows = knowledge_sources_summary(profile)
        if src_rows:
            st.dataframe(src_rows, use_container_width=True, hide_index=True)
        elif profile:
            st.info(
                f"Product `{profile.get('product_id')}` loaded via ETL batch "
                f"`{profile.get('etl_batch_id', 'n/a')}` — "
                f"{profile.get('symptom_count', 0)} symptoms, "
                f"{profile.get('failure_mode_count', 0)} failure modes in graph."
            )
        else:
            st.caption("Run enterprise ETL to attach source lineage metadata.")

    with tab_technical:
        st.markdown("**Reasoning flow (Mermaid)**")
        st.markdown(f"```mermaid\n{reasoning_mermaid(diagnosis)}\n```")
        st.markdown("**Neo4j Cypher**")
        st.code(_neo4j_browser_cypher(diagnosis), language="cypher")


def _render_interactive_graph(
    graph_data: dict | None,
    *,
    graph_key: str,
    height: int = 480,
    caption: str = "",
    physics: bool = False,
) -> None:
    """Force-directed explorer for Knowledge Graph page (engineer view)."""
    if not graph_data or not graph_data.get("nodes"):
        st.caption("No graph data to display.")
        return

    show_key = f"show_graph_{graph_key}"
    if show_key not in st.session_state:
        st.session_state[show_key] = False

    if not st.session_state[show_key]:
        n = graph_data.get("node_count", len(graph_data.get("nodes", [])))
        e = graph_data.get("edge_count", len(graph_data.get("edges", [])))
        if st.button(f"Load explorer graph ({n} nodes, {e} edges)", key=f"btn_{show_key}"):
            st.session_state[show_key] = True
            st.rerun()
        return

    with st.spinner("Rendering…"):
        html = _cached_pyvis_html(
            json.dumps(graph_data, sort_keys=True, default=str),
            height,
            physics,
        )
    if caption:
        st.caption(caption)
    components.html(html, height=height + 40, scrolling=True)
    if st.button("Hide graph", key=f"hide_{show_key}"):
        st.session_state[show_key] = False
        st.rerun()


def _neo4j_browser_cypher(diagnosis: dict) -> str:
    product_id = diagnosis.get("product_id", "")
    symptoms = diagnosis.get("matched_symptoms") or []
    symptom_ids = ", ".join(f"'{s['symptom_id']}'" for s in symptoms[:4])
    top_fm = (diagnosis.get("ranked_failure_modes") or [None])[0]
    fm_id = top_fm.get("failure_mode_id", "") if top_fm else ""
    return f"""// Diagnosis reasoning path (open in Neo4j Browser :7474)
MATCH (p:Product {{product_id: '{product_id}'}})
MATCH (p)-[:HAS_SYMPTOM]->(s:Symptom)
WHERE s.symptom_id IN [{symptom_ids}]
MATCH (s)-[ind:INDICATES]->(fm:FailureMode {{failure_mode_id: '{fm_id}'}})
OPTIONAL MATCH (fm)-[:REQUIRES_PART]->(pt:Part)
OPTIONAL MATCH (r:HistoricalResolution)-[:FOR_PRODUCT]->(p)
OPTIONAL MATCH (r)-[:CONFIRMED]->(fm)
RETURN p, s, ind, fm, pt, r"""


def _strip_traceability_section(text: str) -> str:
    marker = "**Source Traceability:**"
    if marker not in text:
        return text
    return text.split(marker, 1)[0].rstrip()


def _render_provenance(trail: list[dict]) -> None:
    if not trail:
        st.caption("No provenance trail recorded.")
        return
    for entry in enrich_provenance_trail(trail):
        source = entry.get("source_system", "Synthetic")
        record = entry.get("source_record_id", "") or entry.get("entity_id", "")
        entity = entry.get("entity_type", "")
        doc = entry.get("source_document_uri", "")
        detail = doc or record
        st.markdown(f"- **{source}** · `{record}` · {entity} — {detail}")


def _render_source_traceability(trail: list[dict]) -> None:
    if not trail:
        st.caption("No source traceability recorded for this diagnosis.")
        return
    for line in format_traceability_lines(trail):
        st.markdown(line)


def _process_diagnosis_prompt(
    prompt: str,
    *,
    product_id: str | None,
    asset_id: str | None,
    crm_context: dict,
    warranty: dict,
) -> None:
    """Run diagnosis once and append assistant message (no duplicate triggers).

    Business rules (warranty gate, diagnosis, escalation handoff) live in
    services.diagnosis_service so the UI and REST API cannot drift apart.
    """
    with st.spinner("Querying knowledge graph…"):
        outcome = run_full_diagnosis(
            prompt,
            product_id=product_id,
            asset_id=asset_id,
            crm_context=crm_context,
            warranty=warranty,
        )

    if outcome.warranty_blocked:
        st.session_state.messages.append({
            "role": "assistant",
            "content": outcome.response,
            "crm_context": crm_context,
            "warranty": outcome.warranty,
        })
        return

    response = outcome.response
    if outcome.escalated:
        if outcome.case_id:
            response += (
                f"\n\n_Case `{outcome.case_id}` — escalated to human agent "
                "(simulated case management)._"
            )
        else:
            response += "\n\n_Escalated to human agent._"

    active_warranty = warranty if crm_context.get("enriched") else {}
    st.session_state.messages.append({
        "role": "assistant",
        "content": response,
        "diagnosis": outcome.diagnosis,
        "crm_context": crm_context if crm_context.get("enriched") else None,
        "warranty": active_warranty or None,
        "user_prompt": prompt,
    })


@st.fragment
def _render_chat_page(products: list[dict], crm_data: dict) -> None:
    st.subheader("Customer Support Chat")
    st.markdown(
        "Describe your appliance problem. The agent queries the Neo4j knowledge graph "
        "and returns an explainable diagnosis with provenance."
    )

    product_options = {"Auto-detect": None}
    product_options.update({p["name"]: p["product_id"] for p in products})

    with st.expander("CRM Customer Context (optional)", expanded=False):
        customers = crm_data.get("customers", [])
        customer_options = {"None": None}
        customer_options.update({f"{c['name']} ({c['customer_id']})": c["customer_id"] for c in customers})

        assets = crm_data.get("registered_assets", [])
        customer_id = customer_options.get(st.session_state.get("crm_customer", "None"), None)

        filtered_assets = (
            [a for a in assets if a.get("customer_id") == customer_id]
            if customer_id
            else assets
        )
        asset_options = {"None": None}
        asset_options.update({
            f"{a['asset_id']} — {a['product_id']} ({a['serial_number']})": a["asset_id"]
            for a in filtered_assets
        })

        c1, c2 = st.columns(2)
        selected_customer = c1.selectbox("Customer", list(customer_options.keys()), key="crm_customer")
        selected_asset = c2.selectbox("Registered Asset", list(asset_options.keys()), key="crm_asset")

        customer_id = customer_options[selected_customer]
        asset_id = asset_options[selected_asset]

        crm_context: dict = {}
        warranty: dict = {}
        if customer_id or asset_id:
            crm_cache_key = f"{customer_id}|{asset_id}"
            if st.session_state.get("_crm_cache_key") != crm_cache_key:
                st.session_state._crm_cache_key = crm_cache_key
                st.session_state._crm_context = enrich_session_from_crm(
                    customer_id=customer_id,
                    asset_id=asset_id,
                )
                ctx = st.session_state._crm_context
                st.session_state._warranty_context = (
                    check_warranty_eligibility(ctx) if ctx.get("enriched") else {}
                )
            crm_context = st.session_state.get("_crm_context", {})
            warranty = st.session_state.get("_warranty_context", {})
            if crm_context.get("enriched"):
                for warning in crm_context.get("warnings") or []:
                    st.warning(warning)
                st.success(
                    f"CRM enriched: **{crm_context.get('customer_name', 'N/A')}** · "
                    f"Asset `{crm_context.get('asset_id', 'N/A')}` · "
                    f"Product `{crm_context.get('product_id', 'N/A')}`"
                )
                w_color = "normal" if warranty.get("eligible") else "off"
                st.metric(
                    "Warranty",
                    "Eligible" if warranty.get("eligible") else "Not Eligible",
                    warranty.get("reason", ""),
                    delta_color=w_color,
                )
            else:
                st.warning(crm_context.get("reason", "CRM enrichment unavailable — start mock API on :8090"))

    crm_product_id = crm_context.get("product_id") if crm_context.get("enriched") else None
    selected_product = st.selectbox("Appliance (optional)", list(product_options.keys()), key="chat_product")
    explicit_product_id = product_options[selected_product]
    product_id = explicit_product_id or crm_product_id

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "Hello! I'm your diagnostics assistant. "
                    "Tell me what's wrong with your washing machine, dishwasher, or microwave. "
                    "Select a CRM customer/asset above to bind warranty context."
                ),
            }
        ]

    if st.button("Clear chat history", key="clear_chat"):
        st.session_state.messages = st.session_state.messages[:1]
        st.session_state.pop("_chat_proc_key", None)
        st.rerun()

    last_assistant_idx = max(
        (idx for idx, m in enumerate(st.session_state.messages) if m.get("diagnosis")),
        default=-1,
    )

    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            content = msg["content"]
            diagnosis = msg.get("diagnosis") or {}
            trail = diagnosis.get("provenance_trail", [])
            if msg["role"] == "assistant" and trail:
                content = _strip_traceability_section(content)
            st.markdown(content)
            if msg.get("crm_context"):
                with st.expander("CRM Context", expanded=False):
                    st.json(msg["crm_context"])
            if msg.get("warranty"):
                with st.expander("Warranty Eligibility", expanded=False):
                    st.json(msg["warranty"])
            if msg.get("diagnosis"):
                diagnosis = msg["diagnosis"] or {}
                trail = diagnosis.get("provenance_trail", [])
                map_key = f"show_map_{i}"
                is_latest = i == last_assistant_idx
                with st.expander("Diagnosis briefing + evidence", expanded=is_latest):
                    show_graph = is_latest or st.session_state.get(map_key, False)
                    if not is_latest:
                        if st.button("Show reasoning map", key=f"btn_{map_key}"):
                            st.session_state[map_key] = True
                            st.rerun(scope="fragment")
                    _render_diagnosis_explainability(
                        diagnosis,
                        user_prompt=msg.get("user_prompt", ""),
                        crm_context=msg.get("crm_context"),
                        warranty=msg.get("warranty"),
                        graph_key=f"chat_{i}_{_graph_cache_key(diagnosis.get('graph_subgraph') or {})}",
                        show_graph=show_graph,
                    )
                if trail:
                    with st.expander("Source traceability (lineage)", expanded=False):
                        _render_source_traceability(trail)
                msg_asset = asset_id if crm_context.get("enriched") else None
                msg_customer = customer_id if crm_context.get("enriched") else None
                if diagnosis.get("product_id") and msg_asset and crm_context.get("enriched"):
                    if st.button("Submit Warranty Claim", key=f"claim_msg_{i}"):
                        claim = submit_claim_from_diagnosis(
                            diagnosis=diagnosis,
                            asset_id=msg_asset,
                            customer_id=msg_customer or "",
                            user_message=msg.get("user_prompt", msg.get("content", "")),
                        )
                        st.success(f"Claim `{claim['claim_id']}` submitted — status: {claim['status']}")
                with st.expander("Technical payload (JSON)", expanded=False):
                    st.json(diagnosis)
                    # Provenance trail already shown in the dedicated
                    # "Source traceability (lineage)" expander above —
                    # do not repeat it here to avoid duplicate content.

    examples = [
        ("My washing machine won't spin and water stays in the drum", "wm-001"),
        ("Dishwasher leaves dishes wet and cold after the cycle", "dw-001"),
        ("Microwave runs but food stays cold, and I see arcing inside", "mw-001"),
        ("Samsung refrigerator shows 22E and fridge section is warm", "oem-sam-rf28"),
        ("LG dryer shows d90 and clothes are still damp", "oem-lg-dle3400"),
        ("Whirlpool gas range F9 E0 and oven won't heat", "oem-whi-wfg505"),
    ]
    example_labels = [e[0] for e in examples]
    picked = st.selectbox(
        "Example scenarios (select then click Send)",
        ["— pick an example —", *example_labels],
        key="example_pick",
    )
    ex_col1, _ = st.columns([1, 4])
    send_example = ex_col1.button("Send example", disabled=(not picked or picked.startswith("—")), key="send_example_btn")

    user_input = st.chat_input("Describe the problem…")

    prompt: str | None = None
    example_product_id: str | None = None
    if user_input:
        prompt = user_input.strip()
    elif send_example and picked and not picked.startswith("—"):
        prompt = picked
        example_product_id = next((pid for label, pid in examples if label == picked), None)

    if prompt:
        effective_product_id = example_product_id or product_id
        effective_asset_id = asset_id
        effective_crm = dict(crm_context)
        effective_warranty = dict(warranty) if warranty else {}

        detected = detect_product(prompt)
        if (
            detected
            and effective_crm.get("enriched")
            and effective_crm.get("product_id")
            and detected["product_id"] != effective_crm["product_id"]
        ):
            effective_asset_id = None
            effective_crm = {
                **effective_crm,
                "asset_binding_skipped": True,
                "warnings": [
                    *(effective_crm.get("warnings") or []),
                    (
                        f"Example/message targets **{detected['name']}** but CRM asset is "
                        f"**{effective_crm.get('product_id')}**. Asset binding skipped for this turn."
                    ),
                ],
            }
            if not explicit_product_id:
                effective_product_id = None

        has_response = (
            len(st.session_state.messages) >= 2
            and st.session_state.messages[-1]["role"] == "assistant"
            and st.session_state.messages[-2]["role"] == "user"
            and st.session_state.messages[-2]["content"] == prompt
        )
        if not has_response:
            if not (
                st.session_state.messages
                and st.session_state.messages[-1]["role"] == "user"
                and st.session_state.messages[-1]["content"] == prompt
            ):
                st.session_state.messages.append({"role": "user", "content": prompt})
            _process_diagnosis_prompt(
                prompt,
                product_id=effective_product_id,
                asset_id=effective_asset_id,
                crm_context=effective_crm,
                warranty=effective_warranty,
            )


@st.fragment
def _render_claims_page() -> None:
    st.subheader("Warranty Claims")
    st.caption("Claims created from graph-backed diagnoses — parts, BOM impact, and warranty decisions.")

    claims = list_submitted_claims(limit=100)
    if not claims:
        st.info("No claims yet. Run a diagnosis with a CRM asset bound, then **Submit Warranty Claim**.")
        return

    # ── Status summary metrics ────────────────────────────────
    by_status: dict[str, int] = {}
    for c in claims:
        by_status[c.get("status", "unknown")] = by_status.get(c.get("status", "unknown"), 0) + 1

    m_cols = st.columns(min(len(by_status) + 1, 6))
    m_cols[0].metric("Total", len(claims))
    for col, (s, cnt) in zip(m_cols[1:], sorted(by_status.items())):
        col.metric(s.replace("_", " ").title(), cnt)
    st.divider()

    # ── Filter + pagination ────────────────────────────────────
    filter_status_opts = ["all"] + sorted(by_status.keys())
    f1, f2 = st.columns([2, 3])
    filter_val = f1.selectbox("Filter by status", filter_status_opts, key="claims_filter")
    filtered = claims if filter_val == "all" else [c for c in claims if c.get("status") == filter_val]

    page_size = 10
    total_pages = max(1, (len(filtered) + page_size - 1) // page_size)
    page = 1
    if total_pages > 1:
        page = f2.number_input("Page", min_value=1, max_value=total_pages, value=1, key="claims_page")
    offset = (page - 1) * page_size
    page_claims = filtered[offset:offset + page_size]

    if not page_claims:
        st.info("No claims match the current filter.")
        return
    st.caption(f"Showing {offset + 1}–{min(offset + page_size, len(filtered))} of {len(filtered)}")

    # ── Claim cards ───────────────────────────────────────────
    _STATUS_BADGE = {
        "submitted": "badge-submitted", "approved": "badge-approved",
        "denied": "badge-denied",   "closed": "badge-closed",
        "pending_review": "badge-open",
    }
    for claim in page_claims:
        cid = claim.get("claim_id", "unknown")
        cstatus = claim.get("status", "unknown")
        badge_cls = _STATUS_BADGE.get(cstatus, "badge-closed")
        fm_name = claim.get("failure_mode_name") or claim.get("symptom_ids", [""])[0] or "N/A"
        product_name = claim.get("product_name") or claim.get("product_id", "")
        cost = claim.get("estimated_parts_cost_usd") or 0
        cost_str = f"${cost:.2f}" if cost else "no cost"

        with st.expander(
            f"{cid} · {product_name} · {fm_name} · {cost_str}",
            expanded=False,
        ):
            row1, row2 = st.columns([3, 1])
            with row1:
                st.markdown(
                    f"**Asset:** `{claim.get('asset_id') or 'N/A'}` · "
                    f"**Model:** {claim.get('model_number') or 'N/A'} · "
                    f"**Confidence:** {claim.get('diagnosis_confidence', 0):.0%}",
                    unsafe_allow_html=False,
                )
                wc = claim.get("warranty_check") or {}
                warranty_icon = "✅" if wc.get("eligible") else "❌"
                st.caption(
                    f"{warranty_icon} Warranty: {wc.get('reason', 'unknown')} · "
                    f"Submitted {(claim.get('submitted_at') or claim.get('created_at') or '')[:10]}"
                )
            with row2:
                st.markdown(
                    f'<span class="badge {badge_cls}">{cstatus.replace("_", " ").upper()}</span>',
                    unsafe_allow_html=True,
                )

            parts = claim.get("predicted_parts") or []
            if parts:
                st.markdown("**Predicted parts:**")
                for p in parts[:3]:
                    score = p.get("prediction_score", 0)
                    p_cost = p.get("estimated_cost_usd")
                    cost_part = f" · \${p_cost:.2f}" if p_cost else ""
                    st.markdown(
                        f"- {p.get('name')} · `{p.get('part_number')}` · "
                        f"replacement probability {score:.0%}{cost_part}"
                    )

            c1, c2, c3 = st.columns(3)
            if c1.button("✅ Approve", key=f"appr_{cid}", disabled=(cstatus == "approved")):
                update_claim_status(cid, "approved")
                st.cache_data.clear()
                st.rerun(scope="fragment")
            if c2.button("❌ Deny", key=f"deny_{cid}", disabled=(cstatus in ("denied", "closed"))):
                update_claim_status(cid, "denied")
                st.cache_data.clear()
                st.rerun(scope="fragment")
            if c3.button("🔒 Close", key=f"clm_close_{cid}", disabled=(cstatus == "closed")):
                update_claim_status(cid, "closed")
                st.cache_data.clear()
                st.rerun(scope="fragment")

            with st.expander("Full claim detail (JSON)", expanded=False):
                st.json(claim)

    # Pagination at the bottom too for long lists
    if total_pages > 1:
        st.number_input(
            "Page (bottom)", min_value=1, max_value=total_pages, value=page,
            key="claims_page_b", help="Navigate pages",
        )


@st.fragment
def _render_dashboard_page() -> None:
    st.subheader("Human Agent Dashboard")
    st.caption("Escalated cases — critical severity or low-confidence diagnoses requiring human review.")

    c_filter, c_sort = st.columns(2)
    filter_status = c_filter.selectbox(
        "Filter by status",
        ["open", "in_progress", "resolved", "closed", "all"],
        key="dash_filter",
    )
    sort_critical_first = c_sort.checkbox("Critical cases first", value=True, key="dash_sort")

    status_arg = None if filter_status == "all" else filter_status
    cases = list_escalations(status=status_arg, limit=200)

    if not cases:
        st.info("No escalations in this view. Low-confidence or critical diagnoses appear here automatically.")
        return

    # ── Sort: critical severity symptoms first ─────────────────
    def _case_priority(c: dict) -> int:
        diag = c.get("diagnosis") or {}
        syms = diag.get("matched_symptoms") or []
        if any(s.get("severity") == "critical" for s in syms):
            return 0
        fm = (diag.get("ranked_failure_modes") or [{}])[0]
        if fm.get("action_priority") == "High":
            return 1
        return 2

    if sort_critical_first:
        cases = sorted(cases, key=_case_priority)

    open_count = count_escalations(status="open")
    m1, m2, m3 = st.columns(3)
    m1.metric("Showing", len(cases))
    m2.metric("Open (all)", open_count)
    m3.metric("Filter", filter_status)
    st.divider()

    page_size = 15
    total_pages = max(1, (len(cases) + page_size - 1) // page_size)
    page = st.number_input("Page", min_value=1, max_value=total_pages, value=1, key="dash_page")
    offset = (page - 1) * page_size
    st.caption(f"Showing {offset + 1}–{min(offset + page_size, len(cases))} of {len(cases)}")

    _AP_BADGE = {"High": "badge-high", "Medium": "badge-medium", "Low": "badge-low"}
    _STATUS_BADGE = {
        "open": "badge-open", "in_progress": "badge-in-progress",
        "resolved": "badge-resolved", "closed": "badge-closed",
    }

    for case in cases[offset:offset + page_size]:
        diagnosis = case.get("diagnosis") or {}
        case_id = case.get("case_id", "unknown")
        case_status = case.get("status", "open")
        syms = diagnosis.get("matched_symptoms") or []
        is_critical = any(s.get("severity") == "critical" for s in syms)
        top_fm = (diagnosis.get("ranked_failure_modes") or [{}])[0]
        ap = top_fm.get("action_priority", "")

        # Coloured left border for critical / high-AP cases (via CSS class; kept
        # for future expander-wrapper use — CSS classes shown in badge row below).

        with st.expander(
            f"[{case_status.upper()}] {case_id} · "
            f"{diagnosis.get('product_name', 'Unknown')} · "
            f"{case.get('created_at', '')[:10]}",
            expanded=False,
        ):
            # ── Case header badges ──────────────────────────────
            badge_status = _STATUS_BADGE.get(case_status, "badge-closed")
            badge_ap = _AP_BADGE.get(ap, "")
            badges_html = f'<span class="badge {badge_status}">{case_status.replace("_", " ").upper()}</span>'
            if ap:
                badges_html += f' &nbsp;<span class="badge {badge_ap}">AP {ap}</span>'
            if is_critical:
                badges_html += ' &nbsp;<span class="badge badge-high">CRITICAL SYMPTOM</span>'
            st.markdown(badges_html, unsafe_allow_html=True)

            # ── Safety warning for critical cases ───────────────
            if is_critical:
                safety = top_fm.get("safety_notes") or ""
                if safety:
                    st.warning(f"🚨 **Safety:** {safety}")

            st.markdown(f"**Customer:** {case.get('user_message', '')[:120]}")
            st.markdown(f"**Reason:** {diagnosis.get('escalation_reason', 'N/A')}")

            # ── Diagnosis summary for agent ─────────────────────
            conf = diagnosis.get("confidence", 0)
            gc = diagnosis.get("graph_confidence", 0)
            lc = diagnosis.get("language_confidence", 0)
            if top_fm.get("name"):
                rpn = top_fm.get("rpn", "")
                posterior = float(top_fm.get("posterior", conf))
                st.markdown(
                    f"**Top diagnosis:** {top_fm['name']} · "
                    f"posterior {posterior:.0%} · graph edge {gc:.0%} · language {lc:.0%}"
                    + (f" · RPN {rpn}" if rpn else "")
                )

            # ── Matched symptoms summary ────────────────────────
            if syms:
                sym_lines = [
                    f"- {s.get('description', '')} • "
                    f"severity **{s.get('severity','')}** • "
                    f"match {s.get('match_score', 0):.0%}"
                    for s in syms[:3]
                ]
                st.markdown("**Matched symptoms:**\n" + "\n".join(sym_lines))

            # ── Provenance trail ────────────────────────────────
            trail = diagnosis.get("provenance_trail", [])
            if trail:
                with st.expander("Source provenance", expanded=False):
                    _render_provenance(trail)

            # ── Action buttons ──────────────────────────────────
            col_a, col_b, col_c = st.columns(3)
            if col_a.button("▶ In Progress", key=f"prog_{case_id}",
                            disabled=(case_status == "in_progress")):
                update_escalation_status(case_id, "in_progress")
                st.cache_data.clear()
                st.rerun(scope="fragment")
            if col_b.button("✅ Resolve", key=f"res_{case_id}",
                            disabled=(case_status in ("resolved", "closed"))):
                update_escalation_status(case_id, "resolved")
                st.cache_data.clear()
                st.rerun(scope="fragment")
            if col_c.button("🔒 Close", key=f"close_{case_id}",
                            disabled=(case_status == "closed")):
                update_escalation_status(case_id, "closed")
                st.cache_data.clear()
                st.rerun(scope="fragment")

            with st.expander("Raw case data (debug)", expanded=False):
                st.json(case)


@st.fragment
def _render_graph_page(products: list[dict]) -> None:
    from graph.graph_rag import list_failure_modes, match_symptoms
    from graph.graph_visualization import ontology_mermaid_diagram, product_graph_summary

    st.subheader("Knowledge Graph Explorer")
    st.caption("Neo4j powers all diagnosis. Pick a view below — heavy graphs load only when you ask.")

    product_labels = {p["name"]: p["product_id"] for p in products}
    tab_schema, tab_product, tab_path = st.tabs([
        "📐 Ontology schema",
        "📦 Product knowledge",
        "🔍 Diagnosis path lab",
    ])

    with tab_schema:
        st.markdown("**How the knowledge is structured** — entity types and relationships ingested from PIM, FMEA, FSM, Claims.")
        # Use 680px so the full ER diagram renders without scrolling
        components.html(
            _cached_mermaid_html(ontology_mermaid_diagram(), "Neo4j knowledge graph ontology"),
            height=700,
            scrolling=True,
        )
        with st.expander("Interactive schema explorer (advanced)", expanded=False):
            ontology = _cached_ontology_schema()
            if st.button("Load force-directed schema", key="load_ontology_force"):
                st.session_state["show_ontology_force"] = True
            if st.session_state.get("show_ontology_force"):
                _render_interactive_graph(ontology, graph_key="ontology", height=420, physics=False)

    with tab_product:
        selected = st.selectbox("Product", list(product_labels.keys()), key="graph_product")
        pid = product_labels[selected]
        if st.button("Load product knowledge map", type="primary", key="load_product_graph"):
            st.session_state["product_graph_pid"] = pid
            st.session_state["product_graph_name"] = selected

        if st.session_state.get("product_graph_pid") == pid:
            subgraph = _cached_product_subgraph(pid)
            counts = product_graph_summary(subgraph)
            mcols = st.columns(min(len(counts), 5) or 1)
            for col, (label, count) in zip(mcols, sorted(counts.items())):
                col.metric(label, count)
            with st.spinner("Rendering product map…"):
                html = _cached_product_knowledge_html(
                    json.dumps(subgraph, sort_keys=True, default=str),
                    selected,
                    520,
                )
            components.html(html, height=680, scrolling=True)
        else:
            st.info("Select a product and click **Load product knowledge map**.")

        with st.expander("Failure modes & diagnostic steps", expanded=False):
            c1, c2 = st.columns(2)
            with c1:
                for fm in list_failure_modes(pid)[:8]:
                    st.markdown(f"- **{fm['name']}**")
            with c2:
                from graph.graph_rag import get_diagnostic_steps
                # Use sequential numbering (1, 2…) not the graph step_order.
                for display_num, step in enumerate(get_diagnostic_steps(pid)[:6], 1):
                    st.markdown(f"{display_num}. {step['description'][:70]}")

    with tab_path:
        st.markdown(
            "**Simulate a customer message** → see which symptoms match → visualize the diagnosis path."
        )
        cypher_product = st.selectbox("Product", list(product_labels.keys()), key="cypher_product")
        cypher_pid = product_labels[cypher_product]
        sample_msg = st.text_input(
            "Customer message",
            value="My washing machine won't spin and water stays in the drum",
            key="cypher_msg",
        )
        fm_options = list_failure_modes(cypher_pid)
        fm_labels = {f"{fm['name']}": fm["failure_mode_id"] for fm in fm_options}
        selected_fm = st.selectbox(
            "Failure mode to explore",
            list(fm_labels.keys()) if fm_labels else ["—"],
            key="cypher_fm",
        )
        fm_id = fm_labels.get(selected_fm, "")

        if st.button("Analyze & draw diagnosis path", type="primary", key="run_cypher_viz"):
            matched = match_symptoms(cypher_pid, sample_msg)
            symptom_ids = [s["symptom_id"] for s in matched]
            st.session_state["cypher_explorer"] = {
                "product_id": cypher_pid,
                "symptom_ids": symptom_ids,
                "matched": matched,
                "failure_mode_id": fm_id,
            }

        explorer = st.session_state.get("cypher_explorer") or {}
        if explorer.get("product_id") == cypher_pid:
            matched = explorer.get("matched") or []
            symptom_ids = explorer.get("symptom_ids") or []
            if matched:
                st.markdown("**Matched symptoms (Neo4j graph retrieval)**")
                for s in matched[:4]:
                    st.markdown(
                        f"- {s.get('description')} — match **{s.get('match_score', 0):.0%}** · severity {s.get('severity', '?')}"
                    )
            else:
                st.warning("No symptoms matched — try a more specific message.")

            if symptom_ids and fm_id:
                g = _cached_diagnosis_subgraph(cypher_pid, ",".join(symptom_ids), fm_id)
                # Run real failure-mode ranking to get FMEA/posterior for the map
                from graph.graph_rag import rank_failure_modes_with_error_codes
                ranked_fms = rank_failure_modes_with_error_codes(cypher_pid, symptom_ids, [])
                top_ranked = next((r for r in ranked_fms if r["failure_mode_id"] == fm_id), None)
                if top_ranked:
                    path_conf = float(top_ranked.get("posterior", 0))
                elif matched:
                    path_conf = float(matched[0].get("match_score", 0))
                else:
                    path_conf = 0.0
                pseudo_diag = {
                    "product_name": cypher_product,
                    "product_id": cypher_pid,
                    "matched_symptoms": matched,
                    "ranked_failure_modes": ranked_fms[:3] if ranked_fms else [{"name": selected_fm, "failure_mode_id": fm_id}],
                    "confidence": path_conf,
                    "should_escalate": False,
                }
                _render_executive_reasoning_graph(
                    g,
                    graph_key=f"cypher_{cypher_pid}_{fm_id}",
                    diagnosis=pseudo_diag,
                )
                st.code(
                    f"MATCH (p:Product {{product_id: '{cypher_pid}'}})\n"
                    f"MATCH (p)-[:HAS_SYMPTOM]->(s:Symptom)\n"
                    f"WHERE s.symptom_id IN {symptom_ids}\n"
                    f"MATCH (s)-[ind:INDICATES]->(fm:FailureMode {{failure_mode_id: '{fm_id}'}})\n"
                    f"RETURN p, s, ind, fm",
                    language="cypher",
                )


@st.fragment
def _render_enterprise_page() -> None:
    st.subheader("Enterprise Systems & Pipelines")
    st.caption(
        "ETL lineage, connector health, and simulated case handoffs. "
        "Run `./run_enterprise_demo.sh` for the full stack."
    )

    e1, e2, e3 = st.columns(3)
    e1.metric("Provenance", "Enabled" if settings.enable_provenance else "Disabled")
    e2.metric("Mock Enterprise API", ":8090")
    e3.metric("Diagnostics API", f":{settings.api_port}")

    # Assign to a distinct name so the loop variable 'batch_status' below
    # does not shadow this dict.
    integration_status_data = integration_status()
    with st.expander("Integration health & configuration", expanded=False):
        cfg1, cfg2, cfg3, cfg4 = st.columns(4)
        cfg1.metric("Demo mode", "On" if integration_status_data["demo_mode"] else "Off")
        cfg2.metric("Fixture fallback", "On" if integration_status_data["fixture_fallback"] else "Off")
        cfg3.metric("Hybrid matching", "On" if integration_status_data["hybrid_symptom_matching"] else "Off")
        cfg4.metric("Persistence", Path(integration_status_data["persistence"]).name)

        connector_rows = []
        for name, row in integration_status_data["connectors"].items():
            reachable = "✅" if row.get("reachable") else "❌"
            mode_raw = row.get("mode", "—")
            # Make mode strings more readable
            mode_display = {
                "fixture_fallback": "Fixture (local)",
                "mock": "Mock HTTP",
                "live": "Live",
                "production": "Production",
            }.get(mode_raw, mode_raw)
            connector_rows.append({
                "Connector": name.upper(),
                "Mode": mode_display,
                "Status": reachable,
                "Detail": str(row.get("detail", ""))[:60],
            })
        st.dataframe(connector_rows, use_container_width=True, hide_index=True)

    st.markdown("### ETL Lineage Batches")
    all_batches = list_batches(limit=50)
    show_history = st.checkbox("Show full pipeline history", value=False)

    if not all_batches:
        st.info("No ETL batches logged yet. Run: `python -m graph.enterprise_pipeline.orchestrator`")
    else:
        success_count = sum(1 for b in all_batches if b.get("status") == "success")
        failed_count = sum(1 for b in all_batches if b.get("status") == "failed")
        latest_success = next((b for b in all_batches if b.get("status") == "success"), None)
        if latest_success:
            st.success(
                f"Latest: **{latest_success.get('pipeline')}** at "
                f"{latest_success.get('timestamp', '')[:19]} · "
                f"{success_count} succeeded / {failed_count} failed in log"
            )
        else:
            st.warning(f"No successful pipeline steps yet · {failed_count} failed entries")

        batches = (
            all_batches if show_history
            else ([b for b in all_batches if b.get("status") == "success"][:6] or all_batches[:6])
        )

        # ── Confirmation-gated clear button ───────────────────
        if st.checkbox("🗑️ Enable lineage log clearing", key="allow_clear_lineage", value=False):
            if st.button("Clear lineage log", key="clear_lineage", type="primary"):
                lineage_file = settings.lineage_dir / "etl_batches.jsonl"
                if lineage_file.exists():
                    lineage_file.unlink()
                st.cache_data.clear()
                st.rerun(scope="fragment")

        for batch in batches:
            batch_status = batch.get("status", "unknown")
            icon = _batch_status_icon(batch_status)
            pipeline = batch.get("pipeline", "unknown")
            with st.expander(
                f"{icon} {pipeline} · {batch_status} · {batch.get('timestamp', '')[:19]}",
                expanded=(batch_status == "failed" and show_history),
            ):
                b1, b2 = st.columns(2)
                b1.markdown(f"**Batch ID:** `{batch.get('batch_id')}`")
                b2.markdown(
                    f"**Products:** {batch.get('product_count', 0)} · "
                    f"**Target:** {batch.get('neo4j_target', 'N/A')}"
                )
                sources = batch.get("sources")
                if sources:
                    lbl = "Connector sources:" if pipeline == "knowledge_etl" else "Run details:"
                    st.markdown(f"**{lbl}**")
                    for src_name, src in sources.items():
                        st.markdown(f"- **{src_name}:** {_format_batch_source(src_name, src)}")
                if batch.get("errors"):
                    st.error("; ".join(str(e) for e in batch["errors"]))
                with st.expander("Raw JSON (debug)", expanded=False):
                    st.json(batch)

    st.markdown("### Simulated Case Management")
    sim_cases = _load_simulated_cases()
    if not sim_cases:
        st.info(
            "No cases in simulated CCaaS yet. Bind CRM in **Customer Chat**, "
            "trigger an escalation, and a case appears when the mock API is running."
        )
    else:
        for case in sim_cases[:10]:
            diag = case.get("diagnosis", {})
            with st.expander(
                f"[{case.get('status', 'open').upper()}] {case.get('case_id')} — "
                f"{case.get('customer_id')} / {case.get('asset_id')}"
            ):
                st.markdown(f"**Message:** {case.get('user_message', '')[:120]}")
                st.markdown(f"**Reason:** {case.get('escalation_reason', diag.get('escalation_reason', 'N/A'))}")
                st.json(case)

    st.markdown("### Pipeline Commands")
    st.code(
        "./run_enterprise_demo.sh\n"
        "python -m graph.enterprise_pipeline.orchestrator\n"
        'curl -X POST http://localhost:8080/diagnose -H "Content-Type: application/json" '
        '-d \'{"message":"washer won\'"\'"\'t spin","asset_id":"AST-WM-4421"}\'',
        language="bash",
    )


# ── Main layout ───────────────────────────────────────────────────────────────

inject_theme()

neo4j_ok = _cached_neo4j_ok()
mock_ok = _cached_mock_ok()
open_cases = _cached_open_escalations()

with st.sidebar:
    st.markdown("### Diagnostics Platform")
    if "nav_page" not in st.session_state:
        st.session_state.nav_page = PAGES[0]
    page = st.radio("Navigate", PAGES, key="nav_page", label_visibility="collapsed")
    st.caption(PAGE_HELP.get(page, ""))
    st.divider()
    st.markdown("**System status**")
    st.metric("Neo4j", "Connected" if neo4j_ok else "Offline")
    st.metric("Mock APIs", "Online" if mock_ok else "Offline")
    st.metric("Open escalations", open_cases)
    if settings.demo_mode:
        st.caption(f"Demo mode · fixtures + `{settings.mock_enterprise_api_url}`")

st.markdown(
    f"""<div class="diag-hero">
      <h1>Enterprise Diagnostics Chatbot</h1>
      <p>Explainable appliance diagnosis — <strong>Neo4j GraphRAG</strong> does the reasoning;
      <strong>LangGraph</strong> orchestrates the workflow. Every answer shows evidence, sources, and a reasoning map.</p>
      <div class="diag-pill-row">
        <span class="diag-pill">Neo4j · live graph queries</span>
        <span class="diag-pill">LangGraph · detect → diagnose → escalate</span>
        <span class="diag-pill">No LLM required for demo</span>
        <span class="diag-pill">CRM · Claims · PIM · FSM</span>
      </div>
    </div>""",
    unsafe_allow_html=True,
)

if not neo4j_ok:
    st.error(
        "Neo4j is not reachable. Start it with: `docker start neo4j-demo` "
        "then run `PYTHONPATH=. python graph/populate_graph.py`"
    )
    st.stop()

with st.expander("How this platform works (read this first)", expanded=False):
    st.markdown(f"```mermaid\n{platform_journey_mermaid()}\n```")
    col_lg, col_faq = st.columns([1, 1])
    with col_lg:
        st.markdown("**LangGraph workflow** _(orchestration only — not the brain)_")
        st.markdown(f"```mermaid\n{langgraph_workflow_mermaid()}\n```")
    with col_faq:
        st.markdown(architecture_faq_markdown())

j1, j2, j3, j4 = st.columns(4)
j1.markdown('<div class="diag-step-card"><strong>1 · You ask</strong><span>Describe symptoms or pick an example scenario.</span></div>', unsafe_allow_html=True)
j2.markdown('<div class="diag-step-card"><strong>2 · LangGraph runs</strong><span>Detect product, query graph, format answer, escalate if needed.</span></div>', unsafe_allow_html=True)
j3.markdown('<div class="diag-step-card"><strong>3 · Neo4j reasons</strong><span>Match symptoms, rank failure modes, parts, steps, provenance.</span></div>', unsafe_allow_html=True)
j4.markdown('<div class="diag-step-card"><strong>4 · You review</strong><span>Reasoning map, evidence trail, agent queue if escalated.</span></div>', unsafe_allow_html=True)

st.divider()

products = _cached_products()
crm_data = _cached_crm_fixtures()

if page == PAGES[0]:
    _render_chat_page(products, crm_data)
elif page == PAGES[1]:
    _render_claims_page()
elif page == PAGES[2]:
    _render_dashboard_page()
elif page == PAGES[3]:
    _render_graph_page(products)
else:
    _render_enterprise_page()