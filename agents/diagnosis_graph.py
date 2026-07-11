"""
LangGraph diagnosis workflow (works without external LLM — graph-native demo mode).
"""

from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from agents.tools import tool_diagnose
from graph.graph_rag import DiagnosisResult, diagnose
from utils.escalation_store import save_escalation
from utils.logger import get_logger

logger = get_logger(__name__)


class AgentState(TypedDict, total=False):
    user_message: str
    product_id: str | None
    asset_id: str | None
    crm_product_id: str | None
    crm_context: dict[str, Any] | None
    force_keep_context: bool
    product_name: str | None
    diagnosis: dict[str, Any] | None
    response: str
    escalated: bool
    case_id: str | None
    context_block_code: str


def node_detect_product(state: AgentState) -> AgentState:
    from graph.graph_rag import resolve_product_for_diagnosis

    product, _, effective_asset_id, _warnings, block_code, _meta = resolve_product_for_diagnosis(
        state["user_message"],
        product_id=state.get("product_id"),
        asset_id=state.get("asset_id"),
        crm_product_id=state.get("crm_product_id"),
        force_keep_context=bool(state.get("force_keep_context")),
        crm_context=state.get("crm_context"),
    )
    if block_code:
        return {
            **state,
            # Keep bound product for soft mismatch messaging (asset-first product)
            "product_id": (product["product_id"] if product else state.get("product_id")),
            "product_name": product["name"] if product else state.get("product_name"),
            "asset_id": effective_asset_id if block_code.startswith("soft_") else state.get("asset_id"),
            "context_block_code": block_code,
        }
    return {
        **state,
        "product_id": product["product_id"] if product else state.get("product_id"),
        "product_name": product["name"] if product else state.get("product_name"),
        "asset_id": effective_asset_id,
        "context_block_code": "",
    }


def node_run_graph_diagnosis(state: AgentState) -> AgentState:
    payload = tool_diagnose(
        state["user_message"],
        product_id=state.get("product_id"),
        asset_id=state.get("asset_id"),
        crm_product_id=state.get("crm_product_id"),
        force_keep_context=bool(state.get("force_keep_context")),
        crm_context=state.get("crm_context"),
    )
    return {**state, "diagnosis": payload}


def node_format_response(state: AgentState) -> AgentState:
    diagnosis = state.get("diagnosis") or {}
    response = diagnosis.get("formatted_response", "Unable to generate diagnosis.")
    return {**state, "response": response}


def node_handle_escalation(state: AgentState) -> AgentState:
    diagnosis = state.get("diagnosis") or {}
    if not diagnosis.get("should_escalate"):
        return {**state, "escalated": False, "case_id": None}

    case = save_escalation(state["user_message"], diagnosis, status="open")
    logger.info("Escalated case %s", case["case_id"])
    return {**state, "escalated": True, "case_id": case["case_id"]}


def build_diagnosis_graph():
    graph = StateGraph(AgentState)
    graph.add_node("detect_product", node_detect_product)
    graph.add_node("run_diagnosis", node_run_graph_diagnosis)
    graph.add_node("format_response", node_format_response)
    graph.add_node("handle_escalation", node_handle_escalation)

    graph.set_entry_point("detect_product")
    graph.add_edge("detect_product", "run_diagnosis")
    graph.add_edge("run_diagnosis", "format_response")
    graph.add_edge("format_response", "handle_escalation")
    graph.add_edge("handle_escalation", END)

    return graph.compile()


_diagnosis_app = None


def get_diagnosis_app():
    global _diagnosis_app
    if _diagnosis_app is None:
        _diagnosis_app = build_diagnosis_graph()
    return _diagnosis_app


def run_diagnosis(
    user_message: str,
    product_id: str | None = None,
    asset_id: str | None = None,
    crm_product_id: str | None = None,
    force_keep_context: bool = False,
    crm_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run the full LangGraph diagnosis pipeline."""
    app = get_diagnosis_app()
    initial: AgentState = {
        "user_message": user_message,
        "product_id": product_id,
        "asset_id": asset_id,
        "crm_product_id": crm_product_id,
        "force_keep_context": force_keep_context,
        "crm_context": crm_context,
        "product_name": None,
        "diagnosis": None,
        "response": "",
        "escalated": False,
        "case_id": None,
        "context_block_code": "",
    }
    final = app.invoke(initial)
    return {
        "response": final["response"],
        "diagnosis": final.get("diagnosis"),
        "escalated": final.get("escalated", False),
        "case_id": final.get("case_id"),
        "product_id": final.get("product_id"),
        "product_name": final.get("product_name"),
    }


def run_diagnosis_simple(user_message: str, product_id: str | None = None) -> DiagnosisResult:
    """Direct graph diagnosis without LangGraph orchestration (for tests)."""
    return diagnose(user_message, product_id=product_id)
