"""
Enterprise Diagnostics Chatbot Demo — Streamlit UI

Run: streamlit run ui/app.py
"""

import sys
from pathlib import Path

# Ensure project root is on path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from agents.diagnosis_graph import run_diagnosis
from graph.graph_rag import list_products
from graph.neo4j_client import verify_connection
from utils.escalation_store import list_escalations, update_escalation_status

st.set_page_config(
    page_title="Diagnostics Chatbot Demo",
    page_icon="🔧",
    layout="wide",
)

st.title("Enterprise Diagnostics Chatbot Demo")
st.caption("GraphRAG + LangGraph + Neo4j — explainable appliance diagnosis")

neo4j_ok = verify_connection()
col1, col2, col3 = st.columns(3)
col1.metric("Neo4j", "Connected" if neo4j_ok else "Offline")
col2.metric("Mode", "Graph-Native Demo")
escalations = list_escalations()
open_cases = sum(1 for e in escalations if e.get("status") == "open")
col3.metric("Open Escalations", open_cases)

if not neo4j_ok:
    st.error(
        "Neo4j is not reachable. Start it with: `docker start neo4j-demo` "
        "then run `python graph/populate_graph.py`"
    )
    st.stop()

tab_chat, tab_dashboard, tab_graph = st.tabs([
    "Customer Chatbot",
    "Human Agent Dashboard",
    "Knowledge Graph",
])

# ── Customer Chatbot ──────────────────────────────────────────────────────────
with tab_chat:
    st.subheader("Customer Support Chat")
    st.markdown(
        "Describe your appliance problem. The agent queries the Neo4j knowledge graph "
        "and returns an explainable diagnosis."
    )

    products = list_products()
    product_options = {"Auto-detect": None}
    product_options.update({p["name"]: p["product_id"] for p in products})

    selected_product = st.selectbox("Appliance (optional)", list(product_options.keys()))
    product_id = product_options[selected_product]

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "Hello! I'm your diagnostics assistant. "
                    "Tell me what's wrong with your washing machine, dishwasher, or microwave."
                ),
            }
        ]

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("diagnosis"):
                with st.expander("Diagnosis Details"):
                    st.json(msg["diagnosis"])

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
        with st.spinner("Querying knowledge graph..."):
            result = run_diagnosis(prompt, product_id=product_id)

        response = result["response"]
        if result.get("escalated"):
            response += f"\n\n_Case ID: `{result['case_id']}` — escalated to human agent._"

        st.session_state.messages.append({
            "role": "assistant",
            "content": response,
            "diagnosis": result.get("diagnosis"),
        })
        st.rerun()

# ── Human Agent Dashboard ─────────────────────────────────────────────────────
with tab_dashboard:
    st.subheader("Human Agent Dashboard")
    st.markdown("Review escalated cases with full graph-backed diagnostic payloads.")

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