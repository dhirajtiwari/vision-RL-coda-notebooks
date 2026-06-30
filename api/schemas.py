from typing import Any

from pydantic import BaseModel, Field


class DiagnoseRequest(BaseModel):
    message: str
    product_id: str | None = None
    customer_id: str | None = None
    asset_id: str | None = None  # binds model/SKU/BOM for parts prediction


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