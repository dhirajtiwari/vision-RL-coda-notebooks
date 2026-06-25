"""Source provenance models for knowledge graph entities and diagnosis evidence."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

SourceSystem = Literal["PIM", "FSM", "Claims", "CRM", "ServiceManual", "FMEA", "CallCenterKB", "Synthetic"]


class ProvenanceRecord(BaseModel):
    source_system: SourceSystem
    source_record_id: str
    source_document_uri: str = ""
    source_version: str = "1.0"
    ingested_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    approved_by: str = "knowledge-engineering@demo.local"
    approval_status: Literal["approved", "draft", "retired"] = "approved"
    etl_batch_id: str = ""

    def as_graph_props(self) -> dict[str, Any]:
        return self.model_dump()


def default_provenance(
    source_system: SourceSystem,
    record_id: str,
    *,
    document_uri: str = "",
    batch_id: str = "",
) -> dict[str, Any]:
    return ProvenanceRecord(
        source_system=source_system,
        source_record_id=record_id,
        source_document_uri=document_uri,
        etl_batch_id=batch_id,
    ).as_graph_props()


def provenance_evidence_line(entity_type: str, entity_id: str, props: dict[str, Any]) -> dict[str, Any]:
    return {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "source_system": props.get("source_system", "Unknown"),
        "source_record_id": props.get("source_record_id", ""),
        "source_document_uri": props.get("source_document_uri", ""),
        "source_version": props.get("source_version", ""),
        "ingested_at": props.get("ingested_at", ""),
        "approval_status": props.get("approval_status", ""),
    }