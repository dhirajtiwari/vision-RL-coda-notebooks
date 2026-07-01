from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ClaimStatus(str, Enum):
    """Allowed lifecycle states for a warranty claim (API boundary allow-list)."""

    submitted = "submitted"
    pending_review = "pending_review"
    approved = "approved"
    denied = "denied"
    closed = "closed"


class DiagnoseRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    product_id: str | None = Field(default=None, max_length=64)
    customer_id: str | None = Field(default=None, max_length=64)
    asset_id: str | None = Field(default=None, max_length=64)  # binds model/SKU/BOM for parts prediction


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