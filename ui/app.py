"""
Enterprise Diagnostics Chatbot Demo — Streamlit UI

Run: streamlit run ui/app.py
"""

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
from integrations.crm_enrichment import enrich_session_from_crm
from integrations.warranty_eligibility import check_warranty_eligibility
from utils.escalation_store import list_escalations, update_escalation_status
from utils.lineage_store import list_batches

st.set_page_config(
    page_title="Diagnostics Chatbot Demo",
    page_icon="🔧",
    layout="wide",
)

CRM_FIXTURES = settings.enterprise_sources_dir / "crm_assets.json"


def _load_crm_fixtures() -> dict:
    if CRM_FIXTURES.exists():
        return json.loads(CRM_FIXTURES.read_text(encoding="utf-8"))
    return {"customers": [], "registered_assets": []}


def _load_simulated_cases() -> list[dict]:
    path = settings.cases_file
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _mock_api_ok() -> bool:
    try:
        from graph.enterprise_pipeline.http_client import get_json

        get_json(f"{settings.mock_enterprise_api_url.rstrip('/')}/health")
        return True
    except ConnectionError:
        return False


def _render_provenance(trail: list[dict]) -> None:
    if not trail:
        st.caption("No provenance trail recorded.")
        return
    for entry in trail:
        source = entry.get("source_system", "unknown")
        record = entry.get("source_record_id", "")
        entity = entry.get("entity_type", "")
        st.markdown(f"- **{source}** · `{record}` · {entity}")


st.title("Enterprise Diagnostics Chatbot Demo")
st.caption("GraphRAG + LangGraph + Neo4j — explainable appliance diagnosis with enterprise integrations")

neo4j_ok = verify_connection()
mock_ok = _mock_api_ok()
crm_data = _load_crm_fixtures()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Neo4j", "Connected" if neo4j_ok else "Offline")
col2.metric("Mode", "Enterprise" if settings.use_mock_enterprise_apis else "Graph-Native")
col3.metric("Mock APIs", "Online" if mock_ok else "Offline")
escalations = list_escalations()
open_cases = sum(1 for e in escalations if e.get("status") == "open")
col4.metric("Open Escalations", open_cases)

if not neo4j_ok:
    st.error(
        "Neo4j is not reachable. Start it with: `docker start neo4j-demo` "
        "then run `python graph/populate_graph.py` or `python -m graph.enterprise_pipeline.orchestrator`"
    )
    st.stop()

tab_chat, tab_dashboard, tab_graph, tab_enterprise = st.tabs([
    "Customer Chatbot",
    "Human Agent Dashboard",
    "Knowledge Graph",
    "Enterprise Systems",
])

# ── Customer Chatbot ──────────────────────────────────────────────────────────
with tab_chat:
    st.subheader("Customer Support Chat")
    st.markdown(
        "Describe your appliance problem. The agent queries the Neo4j knowledge graph "
        "and returns an explainable diagnosis with provenance."
    )

    products = list_products()
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
    selected_product = st.selectbox("Appliance (optional)", list(product_options.keys()))
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

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("crm_context"):
                with st.expander("CRM Context"):
                    st.json(msg["crm_context"])
            if msg.get("warranty"):
                with st.expander("Warranty Eligibility"):
                    st.json(msg["warranty"])
            if msg.get("diagnosis"):
                with st.expander("Diagnosis Details"):
                    st.json(msg["diagnosis"])
                    trail = (msg["diagnosis"] or {}).get("provenance_trail", [])
                    if trail:
                        st.markdown("**Provenance Trail**")
                        _render_provenance(trail)

    example = st.selectbox(
        "Try an example",
        [
            "",
            "My washing machine won't spin and water stays in the drum",
            "Dishwasher leaves dishes wet and cold after the cycle",
            "Microwave runs but food stays cold, and I see arcing inside",
        ],
    )

    user_input = st.chat_input("Describe the problem...")
    prompt = user_input or (example if example else None)

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})

        active_warranty = warranty if crm_context.get("enriched") else {}
        if active_warranty and not active_warranty.get("eligible"):
            response = f"Warranty check: {active_warranty.get('reason')}. Please contact support for out-of-warranty options."
            st.session_state.messages.append({
                "role": "assistant",
                "content": response,
                "crm_context": crm_context,
                "warranty": active_warranty,
            })
            st.rerun()

        with st.spinner("Querying knowledge graph..."):
            result = run_diagnosis(prompt, product_id=product_id)

        response = result["response"]
        if result.get("escalated"):
            response += f"\n\n_Case ID: `{result['case_id']}` — escalated to human agent._"

        st.session_state.messages.append({
            "role": "assistant",
            "content": response,
            "diagnosis": result.get("diagnosis"),
            "crm_context": crm_context if crm_context.get("enriched") else None,
            "warranty": active_warranty or None,
        })
        st.rerun()

# ── Human Agent Dashboard ─────────────────────────────────────────────────────
with tab_dashboard:
    st.subheader("Human Agent Dashboard")
    st.markdown("Review escalated cases with graph-backed diagnostic payloads and provenance.")

    cases = list_escalations()
    if not cases:
        st.info("No escalations yet. Critical or low-confidence cases appear here automatically.")
    else:
        for case in cases:
            diagnosis = case.get("diagnosis", {})
            with st.expander(
                f"[{case['status'].upper()}] Case {case['case_id']} — "
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
                if col_a.button("Mark In Progress", key=f"prog_{case['case_id']}"):
                    update_escalation_status(case["case_id"], "in_progress")
                    st.rerun()
                if col_b.button("Resolve", key=f"res_{case['case_id']}"):
                    update_escalation_status(case["case_id"], "resolved")
                    st.rerun()
                if col_c.button("Close", key=f"close_{case['case_id']}"):
                    update_escalation_status(case["case_id"], "closed")
                    st.rerun()

                st.json(case)

# ── Knowledge Graph Explorer ──────────────────────────────────────────────────
with tab_graph:
    st.subheader("Knowledge Graph Explorer")
    st.markdown("Browse products and failure modes loaded in Neo4j.")

    for product in products:
        st.markdown(f"### {product['name']}")
        st.markdown(f"_{product['brand']} · {product['category']}_")

        from graph.graph_rag import get_diagnostic_steps, list_failure_modes

        steps = get_diagnostic_steps(product["product_id"])
        failures = list_failure_modes(product["product_id"])

        if failures:
            st.markdown("**Failure Modes:**")
            for fm in failures:
                st.markdown(f"- **{fm['name']}** — {fm['description'][:80]}...")

        if steps:
            st.markdown("**Diagnostic Steps:**")
            for step in steps:
                st.markdown(f"{step['step_order']}. {step['description']}")

        st.divider()

# ── Enterprise Systems ────────────────────────────────────────────────────────
with tab_enterprise:
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
    batches = list_batches(limit=15)
    if not batches:
        st.info(
            "No ETL batches logged yet. Run: `python -m graph.enterprise_pipeline.orchestrator`"
        )
    else:
        for batch in batches:
            status = batch.get("status", "unknown")
            icon = "✅" if status == "success" else "❌" if status == "failed" else "⏳"
            with st.expander(
                f"{icon} {batch.get('batch_id')} — {batch.get('pipeline')} — {batch.get('timestamp', '')[:19]}"
            ):
                st.markdown(f"**Status:** {status} · **Products:** {batch.get('product_count', 0)}")
                st.markdown(f"**Neo4j target:** {batch.get('neo4j_target', 'N/A')}")
                if batch.get("sources"):
                    st.markdown("**Sources:**")
                    for name, src in batch["sources"].items():
                        st.markdown(f"- {name}: {src.get('record_count', 0)} records ({src.get('mode', '')})")
                if batch.get("errors"):
                    st.error("; ".join(batch["errors"]))
                st.json(batch)

    st.markdown("### Simulated Case Management")
    sim_cases = _load_simulated_cases()
    if not sim_cases:
        st.info(
            "No cases in simulated CCaaS yet. Escalations via REST API create cases when mock API is running."
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
        "# Full enterprise demo (mock APIs + ETL + API + UI)\n"
        "./run_enterprise_demo.sh\n\n"
        "# Run pipelines only\n"
        "python -m graph.enterprise_pipeline.orchestrator\n\n"
        "# Quick demo with enterprise ETL\n"
        "USE_ENTERPRISE=true ./run_demo.sh\n\n"
        "# REST API diagnose\n"
        'curl -X POST http://localhost:8080/diagnose \\\n'
        '  -H "Content-Type: application/json" \\\n'
        '  -d \'{"message":"washer won\'"\'"\'t spin","customer_id":"CUST-10042","asset_id":"AST-WM-4421"}\'',
        language="bash",
    )