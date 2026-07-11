from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ClaimStatus(StrEnum):
    """Allowed lifecycle states for a warranty claim (API boundary allow-list)."""

    submitted = "submitted"
    pending_review = "pending_review"
    approved = "approved"
    denied = "denied"
    closed = "closed"


class DiagnoseRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    product_id: str | None = Field(
        default=None,
        max_length=64,
        description="Anonymous session only. Ignored when asset_id binds product from CRM.",
    )
    customer_id: str | None = Field(default=None, max_length=64)
    asset_id: str | None = Field(
        default=None,
        max_length=64,
        description="Registered asset — product + warranty derived from CRM (asset-first).",
    )
    # Operator confirmed soft appliance mismatch — keep bound asset product
    force_keep_context: bool = False


class DiagnoseResponse(BaseModel):
    response: str
    diagnosis: dict[str, Any] | None = None
    escalated: bool = False
    case_id: str | None = None
    crm_context: dict[str, Any] = Field(default_factory=dict)
    warranty: dict[str, Any] = Field(default_factory=dict)
    provenance_trail: list[dict[str, Any]] = Field(default_factory=list)
    graph_subgraph: dict[str, Any] | None = None


class GraphSubgraphResponse(BaseModel):
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]
    node_count: int
    edge_count: int
    # Diagnosis-path explainability (optional; filled by diagnosis-subgraph)
    cypher_queries: list[dict[str, Any]] | None = None
    traversal: list[dict[str, Any]] | None = None
    params: dict[str, Any] | None = None
