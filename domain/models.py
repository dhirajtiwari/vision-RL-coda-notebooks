"""
Typed domain models for the diagnostics application.

The codebase historically passed untyped ``dict[str, Any]`` between layers, which
forced defensive ``.get()`` access and allowed silent shape drift. These Pydantic
models give the core business objects an explicit contract. They are adopted
incrementally at service boundaries; ``.model_dump()`` keeps them compatible with
existing dict consumers and JSON responses.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class WarrantyDecision(BaseModel):
    """Outcome of a warranty eligibility check.

    ``extra="allow"`` preserves policy/coverage detail fields while still
    enforcing the core decision contract (eligibility + reason).
    """

    model_config = ConfigDict(extra="allow")

    eligible: bool
    reason: str = ""
    warranty_status: str | None = None
    source_system: str = "warranty"


class DiagnosisOutcome(BaseModel):
    """
    Result of the full customer-facing diagnosis workflow: warranty gating,
    graph diagnosis, and escalation/case handoff. Shared by the REST API and the
    Streamlit UI so the business rules live in exactly one place.
    """

    response: str
    diagnosis: dict[str, Any] = Field(default_factory=dict)
    escalated: bool = False
    case_id: str | None = None
    warranty_blocked: bool = False
    warranty: dict[str, Any] = Field(default_factory=dict)
    crm_context: dict[str, Any] = Field(default_factory=dict)
