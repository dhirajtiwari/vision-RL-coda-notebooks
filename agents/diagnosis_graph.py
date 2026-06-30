"""
LangGraph diagnosis workflow (works without external LLM — graph-native demo mode).
"""

from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from agents.tools import tool_diagnose, tool_detect_product
from graph.graph_rag import DiagnosisResult, diagnose
from utils.escalation_store import save_escalation
from utils.logger import get_logger

logger = get_logger(__name__)


class AgentState(TypedDict):
    user_message: str
    product_id: str | None
    asset_id: str | None
    product_name: str | None
    diagnosis: dict[str, Any] | None
    response: str
    escalated: bool
    case_id: str | None


def node_detect_product(state: AgentState) -> AgentState:
    product = tool_detect_product(state["user_message"])
    return {
        **state,
        "product_id": product["product_id"] if product else state.get("product_id"),
        "product_name": product["name"] if product else state.get("product_name"),
    }


def node_run_graph_diagnosis(state: AgentState) -> AgentState:
    payload = tool_diagnose(
        state["user_message"],
        product_id=state.get("product_id"),
        asset_id=state.get("asset_id"),
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
) -> dict[str, Any]:
    """Run the full LangGraph diagnosis pipeline."""
    app = get_diagnosis_app()
    initial: AgentState = {
        "user_message": user_message,
        "product_id": product_id,
        "asset_id": asset_id,
        "product_name": None,
        "diagnosis": None,
        "response": "",
        "escalated": False,
        "case_id": None,
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