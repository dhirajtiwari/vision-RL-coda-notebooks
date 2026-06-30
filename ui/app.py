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

from agents.diagnosis_graph import run_diagnosis
from config.settings import settings
from graph.graph_rag import list_products
from graph.neo4j_client import verify_connection
from integrations.case_management import create_case_from_escalation
from integrations.crm_enrichment import enrich_session_from_crm
from integrations.warranty_eligibility import check_warranty_eligibility
from integrations.claims_workflow import list_submitted_claims, submit_claim_from_diagnosis, update_claim_status
from utils.escalation_store import list_escalations, update_escalation_status
from utils.lineage_store import list_batches

st.set_page_config(
    page_title="Diagnostics Chatbot Demo",
    page_icon="🔧",
    layout="wide",
)

PAGES = (
    "Customer Chatbot",
    "Warranty Claims",
    "Human Agent Dashboard",
    "Knowledge Graph",
    "Enterprise Systems",
)

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
def _cached_pyvis_html(graph_json: str, height: int, physics: bool) -> str:
    from graph.graph_visualization import render_pyvis_html

    graph_data = json.loads(graph_json)
    return render_pyvis_html(graph_data, height=f"{height}px", physics=physics)


@st.cache_data(ttl=120, show_spinner=False)
def _cached_ontology_schema() -> dict:
    from graph.graph_visualization import get_ontology_schema

    return get_ontology_schema()


@st.cache_data(ttl=120, show_spinner=False)
def _cached_product_subgraph(product_id: str) -> dict:
    from graph.graph_visualization import get_product_subgraph

    return get_product_subgraph(product_id)


def _graph_cache_key(graph_data: dict) -> str:
    payload = json.dumps(graph_data, sort_keys=True, default=str)
    return hashlib.md5(payload.encode()).hexdigest()[:12]


def _load_simulated_cases() -> list[dict]:
    path = settings.cases_file
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


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


def _render_interactive_graph(
    graph_data: dict | None,
    *,
    graph_key: str,
    height: int = 480,
    caption: str = "",
    physics: bool = False,
) -> None:
    """Lazy-render PyVis only when the user opts in (avoids iframe overload)."""
    if not graph_data or not graph_data.get("nodes"):
        st.caption("No graph data to display.")
        return

    show_key = f"show_graph_{graph_key}"
    if show_key not in st.session_state:
        st.session_state[show_key] = False

    if not st.session_state[show_key]:
        n = graph_data.get("node_count", len(graph_data.get("nodes", [])))
        e = graph_data.get("edge_count", len(graph_data.get("edges", [])))
        if st.button(f"Show interactive graph ({n} nodes, {e} edges)", key=f"btn_{show_key}"):
            st.session_state[show_key] = True
            st.rerun()
        return

    with st.spinner("Rendering graph…"):
        html = _cached_pyvis_html(
            json.dumps(graph_data, sort_keys=True, default=str),
            height,
            physics,
        )
    if caption:
        st.caption(caption)
    st.html(html, height=height + 24, scrolling=True)
    st.caption(
        f"{graph_data.get('node_count', 0)} nodes · "
        f"{graph_data.get('edge_count', 0)} relationships · "
        "drag nodes · scroll to zoom · red = diagnosis path"
    )
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


def _render_provenance(trail: list[dict]) -> None:
    if not trail:
        st.caption("No provenance trail recorded.")
        return
    for entry in trail:
        source = entry.get("source_system", "unknown")
        record = entry.get("source_record_id", "")
        entity = entry.get("entity_type", "")
        st.markdown(f"- **{source}** · `{record}` · {entity}")


def _process_diagnosis_prompt(
    prompt: str,
    *,
    product_id: str | None,
    asset_id: str | None,
    customer_id: str | None,
    crm_context: dict,
    warranty: dict,
) -> None:
    """Run diagnosis once and append assistant message (no duplicate triggers)."""
    active_warranty = warranty if crm_context.get("enriched") else {}
    if active_warranty and not active_warranty.get("eligible"):
        response = (
            f"Warranty check: {active_warranty.get('reason')}. "
            "Please contact support for out-of-warranty options."
        )
        st.session_state.messages.append({
            "role": "assistant",
            "content": response,
            "crm_context": crm_context,
            "warranty": active_warranty,
        })
        return

    with st.spinner("Querying knowledge graph…"):
        result = run_diagnosis(
            prompt,
            product_id=product_id,
            asset_id=asset_id if crm_context.get("enriched") else None,
        )

    response = result["response"]
    if result.get("escalated"):
        response += f"\n\n_Case ID: `{result['case_id']}` — escalated to human agent._"
        if crm_context.get("enriched") and crm_context.get("customer_id") and crm_context.get("asset_id"):
            ccaas = create_case_from_escalation(
                customer_id=crm_context["customer_id"],
                asset_id=crm_context["asset_id"],
                user_message=prompt,
                diagnosis=result.get("diagnosis") or {},
            )
            if ccaas.get("case_id"):
                response += f"\n\n_CCaaS case `{ccaas['case_id']}` created in simulated case management._"

    st.session_state.messages.append({
        "role": "assistant",
        "content": response,
        "diagnosis": result.get("diagnosis"),
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
        asset_options = {"None": None}
        asset_options.update({
            f"{a['asset_id']} — {a['product_id']} ({a['serial_number']})": a["asset_id"]
            for a in assets
        })

        c1, c2 = st.columns(2)
        selected_customer = c1.selectbox("Customer", list(customer_options.keys()), key="crm_customer")
        selected_asset = c2.selectbox("Registered Asset", list(asset_options.keys()), key="crm_asset")

        customer_id = customer_options[selected_customer]
        asset_id = asset_options[selected_asset]

        crm_context: dict = {}
        warranty: dict = {}
        if customer_id or asset_id:
            crm_context = enrich_session_from_crm(customer_id=customer_id, asset_id=asset_id)
            if crm_context.get("enriched"):
                warranty = check_warranty_eligibility(crm_context)
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
    product_id = product_options[selected_product] or crm_product_id

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

    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("crm_context"):
                with st.expander("CRM Context"):
                    st.json(msg["crm_context"])
            if msg.get("warranty"):
                with st.expander("Warranty Eligibility"):
                    st.json(msg["warranty"])
            if msg.get("diagnosis"):
                diagnosis = msg["diagnosis"] or {}
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
                with st.expander("Diagnosis Graph", expanded=False):
                    subgraph = diagnosis.get("graph_subgraph")
                    if subgraph:
                        _render_interactive_graph(
                            subgraph,
                            graph_key=f"chat_{i}_{_graph_cache_key(subgraph)}",
                            caption="Nodes and relationships used for this diagnosis answer.",
                        )
                        with st.expander("Open same query in Neo4j Browser"):
                            st.code(_neo4j_browser_cypher(diagnosis), language="cypher")
                    else:
                        st.caption("Graph subgraph not available for this message.")
                with st.expander("Diagnosis Details"):
                    st.json(diagnosis)
                    trail = diagnosis.get("provenance_trail", [])
                    if trail:
                        st.markdown("**Provenance Trail**")
                        _render_provenance(trail)

    examples = [
        "My washing machine won't spin and water stays in the drum",
        "Dishwasher leaves dishes wet and cold after the cycle",
        "Microwave runs but food stays cold, and I see arcing inside",
        "Samsung refrigerator shows 22E and fridge section is warm",
        "LG dryer shows d90 and clothes are still damp",
        "Whirlpool gas range F9 E0 and oven won't heat",
    ]
    picked = st.selectbox("Example scenarios (select then click Send)", ["— pick an example —", *examples], key="example_pick")
    ex_col1, ex_col2 = st.columns([1, 4])
    send_example = ex_col1.button("Send example", disabled=(not picked or picked.startswith("—")), key="send_example_btn")

    user_input = st.chat_input("Describe the problem…")

    prompt: str | None = None
    if user_input:
        prompt = user_input.strip()
    elif send_example and picked and not picked.startswith("—"):
        prompt = picked

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        _process_diagnosis_prompt(
            prompt,
            product_id=product_id,
            asset_id=asset_id,
            customer_id=customer_id,
            crm_context=crm_context,
            warranty=warranty,
        )


@st.fragment
def _render_claims_page() -> None:
    st.subheader("Warranty Claims — Graph-Backed Submissions")
    st.markdown(
        "Claims are created from diagnosis outcomes with predicted parts, "
        "BOM impact, warranty eligibility, and Neo4j claim nodes."
    )
    claims = list_submitted_claims(limit=30)
    if not claims:
        st.info("No claims submitted yet. Run a diagnosis with a CRM asset bound, then click **Submit Warranty Claim**.")
        return

    for claim in claims:
        cid = claim.get("claim_id", "unknown")
        with st.expander(
            f"[{claim.get('status', 'unknown').upper()}] {cid} — "
            f"{claim.get('failure_mode_name', 'N/A')} — ${claim.get('estimated_parts_cost_usd', 0):.2f}"
        ):
            st.markdown(f"**Asset:** `{claim.get('asset_id')}` · **Model:** {claim.get('model_number', 'N/A')}")
            st.markdown(f"**Confidence:** {claim.get('diagnosis_confidence', 0):.0%}")
            wc = claim.get("warranty_check", {})
            st.markdown(f"**Warranty:** {'Eligible' if wc.get('eligible') else 'Review'} — {wc.get('reason', '')}")
            parts = claim.get("predicted_parts", [])
            if parts:
                st.markdown("**Predicted Parts:**")
                for p in parts[:3]:
                    st.markdown(
                        f"- {p.get('name')} · `{p.get('part_number')}` · "
                        f"score {p.get('prediction_score', 0):.0%}"
                    )
            c1, c2, c3 = st.columns(3)
            if c1.button("Approve", key=f"appr_{cid}"):
                update_claim_status(cid, "approved")
                st.rerun(scope="fragment")
            if c2.button("Deny", key=f"deny_{cid}"):
                update_claim_status(cid, "denied")
                st.rerun(scope="fragment")
            if c3.button("Close", key=f"clm_close_{cid}"):
                update_claim_status(cid, "closed")
                st.rerun(scope="fragment")
            st.json(claim)


@st.fragment
def _render_dashboard_page() -> None:
    st.subheader("Human Agent Dashboard")
    st.markdown("Review escalated cases with graph-backed diagnostic payloads and provenance.")

    cases = list_escalations()
    if not cases:
        st.info("No escalations yet. Critical or low-confidence cases appear here automatically.")
        return

    for case in cases:
        diagnosis = case.get("diagnosis", {})
        case_id = case.get("case_id", "unknown")
        with st.expander(
            f"[{case['status'].upper()}] Case {case_id} — "
            f"{diagnosis.get('product_name', 'Unknown')} — {case['created_at'][:19]}"
        ):
            st.markdown(f"**Customer message:** {case['user_message']}")
            st.markdown(f"**Escalation reason:** {diagnosis.get('escalation_reason', 'N/A')}")
            st.markdown(f"**Confidence:** {diagnosis.get('confidence', 0):.0%}")

            if diagnosis.get("ranked_failure_modes"):
                top = diagnosis["ranked_failure_modes"][0]
                st.markdown(f"**Top failure mode:** {top.get('name')}")
                st.markdown(f"**Safety:** {top.get('safety_notes')}")

            trail = diagnosis.get("provenance_trail", [])
            if trail:
                st.markdown("**Provenance Trail**")
                _render_provenance(trail)

            col_a, col_b, col_c = st.columns(3)
            if col_a.button("Mark In Progress", key=f"prog_{case_id}"):
                update_escalation_status(case_id, "in_progress")
                st.rerun(scope="fragment")
            if col_b.button("Resolve", key=f"res_{case_id}"):
                update_escalation_status(case_id, "resolved")
                st.rerun(scope="fragment")
            if col_c.button("Close", key=f"close_{case_id}"):
                update_escalation_status(case_id, "closed")
                st.rerun(scope="fragment")

            st.json(case)


@st.fragment
def _render_graph_page(products: list[dict]) -> None:
    from graph.graph_rag import get_diagnostic_steps, list_failure_modes, match_symptoms
    from graph.graph_visualization import get_diagnosis_subgraph

    st.subheader("Knowledge Graph Explorer")
    st.markdown(
        "Interactive graph views: ontology schema, product neighborhoods, and diagnosis paths. "
        "Graphs load on demand to keep the UI responsive."
    )

    product_labels = {p["name"]: p["product_id"] for p in products}
    view = st.radio(
        "View",
        ["Ontology (ER Diagram)", "Product Graph", "Cypher Explorer"],
        horizontal=True,
        key="kg_view",
    )

    if view == "Ontology (ER Diagram)":
        st.markdown("**Property-graph schema** — node labels and relationship types.")
        ontology = _cached_ontology_schema()
        _render_interactive_graph(ontology, graph_key="ontology", height=480, physics=False)

    elif view == "Product Graph":
        selected = st.selectbox("Product", list(product_labels.keys()), key="graph_product")
        pid = product_labels[selected]
        if st.button("Load product graph", key="load_product_graph"):
            st.session_state["product_graph_pid"] = pid
        if st.session_state.get("product_graph_pid") == pid:
            subgraph = _cached_product_subgraph(pid)
            _render_interactive_graph(
                subgraph,
                graph_key=f"product_{pid}",
                caption=f"Neighborhood for {selected}.",
            )
        c1, c2 = st.columns(2)
        with c1:
            failures = list_failure_modes(pid)
            if failures:
                st.markdown("**Failure Modes**")
                for fm in failures[:8]:
                    st.markdown(f"- **{fm['name']}**")
        with c2:
            steps = get_diagnostic_steps(pid)
            if steps:
                st.markdown("**Diagnostic Steps**")
                for step in steps[:6]:
                    st.markdown(f"{step['step_order']}. {step['description'][:60]}…")

    else:
        cypher_product = st.selectbox("Product", list(product_labels.keys()), key="cypher_product")
        cypher_pid = product_labels[cypher_product]
        sample_msg = st.text_input(
            "Sample customer message",
            value="My washing machine won't spin and water stays in the drum",
            key="cypher_msg",
        )
        matched = match_symptoms(cypher_pid, sample_msg)
        symptom_ids = [s["symptom_id"] for s in matched]
        st.markdown("**Matched symptoms:** " + (", ".join(symptom_ids) if symptom_ids else "_none_"))

        fm_options = list_failure_modes(cypher_pid)
        fm_labels = {f"{fm['name']} ({fm['failure_mode_id']})": fm["failure_mode_id"] for fm in fm_options}
        selected_fm = st.selectbox("Top failure mode", list(fm_labels.keys()), key="cypher_fm")
        fm_id = fm_labels[selected_fm]

        if st.button("Run diagnosis subgraph query", key="run_cypher_viz"):
            st.session_state["cypher_explorer_graph"] = get_diagnosis_subgraph(
                cypher_pid, symptom_ids=symptom_ids, failure_mode_id=fm_id
            )

        if st.session_state.get("cypher_explorer_graph"):
            g = st.session_state["cypher_explorer_graph"]
            _render_interactive_graph(g, graph_key=f"cypher_{cypher_pid}_{fm_id}")
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
    st.markdown(
        "ETL lineage, simulated case handoffs, and connector status. "
        "Run `./run_enterprise_demo.sh` for the full stack."
    )

    e1, e2, e3 = st.columns(3)
    e1.metric("Provenance", "Enabled" if settings.enable_provenance else "Disabled")
    e2.metric("Mock Enterprise API", settings.mock_enterprise_api_url)
    e3.metric("Diagnostics API", f"http://localhost:{settings.api_port}")

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
                f"Latest successful step: **{latest_success.get('pipeline')}** at "
                f"{latest_success.get('timestamp', '')[:19]} · "
                f"{success_count} succeeded / {failed_count} failed in log"
            )
        else:
            st.warning(f"No successful pipeline steps yet · {failed_count} failed entries in log")

        batches = all_batches if show_history else [b for b in all_batches if b.get("status") == "success"][:6]
        if not batches and not show_history:
            batches = all_batches[:6]

        if st.button("Clear lineage log", key="clear_lineage"):
            lineage_file = settings.lineage_dir / "etl_batches.jsonl"
            if lineage_file.exists():
                lineage_file.unlink()
            st.cache_data.clear()
            st.rerun(scope="fragment")

        for batch in batches:
            status = batch.get("status", "unknown")
            icon = _batch_status_icon(status)
            pipeline = batch.get("pipeline", "unknown")
            with st.expander(
                f"{icon} {pipeline} — {status} — {batch.get('timestamp', '')[:19]}",
                expanded=status == "failed" and show_history,
            ):
                st.markdown(f"**Batch ID:** `{batch.get('batch_id')}`")
                st.markdown(
                    f"**Products:** {batch.get('product_count', 0)} · "
                    f"**Neo4j target:** {batch.get('neo4j_target', 'N/A')}"
                )
                sources = batch.get("sources")
                if sources:
                    label = "Connector sources:" if pipeline == "knowledge_etl" else "Run details:"
                    st.markdown(f"**{label}**")
                    for name, src in sources.items():
                        st.markdown(f"- **{name}:** {_format_batch_source(name, src)}")
                if batch.get("errors"):
                    st.error("; ".join(str(e) for e in batch["errors"]))
                with st.expander("Raw JSON"):
                    st.json(batch)

    st.markdown("### Simulated Case Management")
    sim_cases = _load_simulated_cases()
    if not sim_cases:
        st.info(
            "No cases in simulated CCaaS yet. Bind CRM in **Customer Chatbot**, "
            "trigger an escalation, and a case appears when mock API is running."
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

st.title("Enterprise Diagnostics Chatbot Demo")
st.caption("GraphRAG + LangGraph + Neo4j — explainable appliance diagnosis with enterprise integrations")

neo4j_ok = _cached_neo4j_ok()
mock_ok = _cached_mock_ok()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Neo4j", "Connected" if neo4j_ok else "Offline")
col2.metric("Mode", "Enterprise" if settings.use_mock_enterprise_apis else "Graph-Native")
col3.metric("Mock APIs", "Online" if mock_ok else "Offline")
open_cases = sum(1 for e in list_escalations() if e.get("status") == "open")
col4.metric("Open Escalations", open_cases)

if not neo4j_ok:
    st.error(
        "Neo4j is not reachable. Start it with: `docker start neo4j-demo` "
        "then run `PYTHONPATH=. python graph/populate_graph.py`"
    )
    st.stop()

if "nav_page" not in st.session_state:
    st.session_state.nav_page = PAGES[0]

page = st.radio(
    "Section",
    PAGES,
    horizontal=True,
    key="nav_page",
    label_visibility="collapsed",
)

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