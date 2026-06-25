from typing import Any

from pydantic import BaseModel, Field


class DiagnoseRequest(BaseModel):
    message: str
    product_id: str | None = None
    customer_id: str | None = None
    asset_id: str | None = None


class DiagnoseResponse(BaseModel):
    response: str
    diagnosis: dict[str, Any] | None = None
    escalated: bool = False
    case_id: str | None = None
    crm_context: dict[str, Any] = Field(default_factory=dict)
    warranty: dict[str, Any] = Field(default_factory=dict)
    provenance_trail: list[dict[str, Any]] = Field(default_factory=list)