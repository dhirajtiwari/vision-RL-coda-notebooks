"""Source provenance models for knowledge graph entities and diagnosis evidence.

Provenance is modelled after the W3C PROV-O data model (Entity / Activity /
Agent): each record is a provenance *Entity* that ``wasGeneratedBy`` an ETL
*Activity* (``prov_activity``) and ``wasAttributedTo`` an *Agent*
(``approved_by``). All lineage in this demo is synthetic, so records carry an
explicit ``simulated`` flag rather than implying a live enterprise extract.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from functools import lru_cache
from typing import Any, Literal

from pydantic import BaseModel, Field

from config.settings import settings

SourceSystem = Literal["PIM", "FSM", "Claims", "CRM", "ServiceManual", "FMEA", "CallCenterKB", "Synthetic"]


class ProvenanceRecord(BaseModel):
    source_system: SourceSystem
    source_record_id: str
    source_document_uri: str = ""
    source_version: str = "1.0"
    ingested_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    approved_by: str = "knowledge-engineering@demo.local"
    approval_status: Literal["approved", "draft", "retired"] = "approved"
    etl_batch_id: str = ""
    # PROV-O: the Activity that generated this Entity.
    prov_activity: str = "knowledge_etl"
    # Honesty flag: all lineage in this demo is synthetic, not a live extract.
    simulated: bool = True

    def as_graph_props(self) -> dict[str, Any]:
        return self.model_dump()


@lru_cache(maxsize=1)
def _load_manifest() -> dict[str, Any]:
    path = settings.provenance_manifest_file
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


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


def manifest_provenance_for_entity(entity_type: str, entity_id: str) -> dict[str, Any]:
    """Fallback provenance when catalog/Neo4j nodes lack lineage metadata."""
    manifest = _load_manifest()
    defaults = manifest.get("entity_defaults", {}).get(entity_type, {})
    sources = manifest.get("sources", {})
    source_key = defaults.get("source_system", "Synthetic")
    base_uri = sources.get(source_key, {}).get("base_uri", "")
    document_uri = f"{base_uri.rstrip('/')}/{entity_id}" if base_uri else ""
    return {
        "source_system": source_key,
        "source_record_id": entity_id,
        "source_document_uri": document_uri,
        "source_version": manifest.get("version", "1.0"),
        "approval_status": defaults.get("approval_status", "approved"),
        "approved_by": defaults.get("approved_by", "knowledge-engineering@demo.local"),
        "ingested_at": datetime.now(UTC).isoformat(),
        "simulated": True,
    }


def _has_source_system(props: dict[str, Any]) -> bool:
    value = (props.get("source_system") or "").strip()
    return bool(value) and value.lower() != "unknown"


def enrich_entity_props(entity_type: str, entity_id: str, props: dict[str, Any]) -> dict[str, Any]:
    """Fill missing provenance fields from manifest defaults at read/format time."""
    if _has_source_system(props):
        enriched = dict(props)
        enriched.setdefault("source_record_id", entity_id)
        enriched.setdefault(
            "source_document_uri",
            manifest_provenance_for_entity(entity_type, entity_id).get("source_document_uri", ""),
        )
        return enriched
    return {**props, **manifest_provenance_for_entity(entity_type, entity_id)}


def provenance_evidence_line(entity_type: str, entity_id: str, props: dict[str, Any]) -> dict[str, Any]:
    enriched = enrich_entity_props(entity_type, entity_id, props)
    return {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "source_system": enriched.get("source_system", "Unknown"),
        "source_record_id": enriched.get("source_record_id", entity_id),
        "source_document_uri": enriched.get("source_document_uri", ""),
        "source_version": enriched.get("source_version", ""),
        "ingested_at": enriched.get("ingested_at", ""),
        "approval_status": enriched.get("approval_status", ""),
    }
