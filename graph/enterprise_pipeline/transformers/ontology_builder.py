"""
Transform enterprise source records into validated knowledge-graph ontology JSON.
"""

from __future__ import annotations

import json
from typing import Any

from config.settings import settings
from graph.enterprise_pipeline.connectors.base import ConnectorResult
from graph.provenance import default_provenance
from graph.synthetic_data_generator import (
    DiagnosticStep,
    FailureMode,
    FailureModePartLink,
    HistoricalResolution,
    KnowledgeGraphData,
    Part,
    Product,
    ProductKnowledge,
    Symptom,
    SymptomFailureLink,
)


class OntologyBuilder:
    """Build ProductKnowledge instances from normalized connector payloads."""

    def __init__(self, etl_batch_id: str = ""):
        self.etl_batch_id = etl_batch_id
        self._manifest = self._load_manifest()

    def _load_manifest(self) -> dict[str, Any]:
        if settings.provenance_manifest_file.exists():
            return json.loads(settings.provenance_manifest_file.read_text(encoding="utf-8"))
        return {"entity_defaults": {}, "sources": {}}

    def build(
        self,
        pim: ConnectorResult,
        fsm: ConnectorResult,
        claims: ConnectorResult,
        crm: ConnectorResult | None = None,
    ) -> KnowledgeGraphData:
        del crm
        products = [self._transform_product(p, fsm.records, claims.records) for p in pim.records]
        return KnowledgeGraphData(products=products)

    def build_catalog_payload(
        self,
        pim: ConnectorResult,
        fsm: ConnectorResult,
        claims: ConnectorResult,
        crm: ConnectorResult | None = None,
    ) -> dict[str, Any]:
        graph_data = self.build(pim, fsm, claims, crm)
        provenance: dict[str, dict[str, Any]] = {}
        for item in graph_data.products:
            pid = item.product.product_id
            provenance[pid] = self._prov("PIM", f"product-{pid}", f"manuals/{pid}/catalog.pdf", "Product")
            for s in item.symptoms:
                provenance[s.symptom_id] = self._prov("FMEA", s.symptom_id, f"manuals/{pid}/symptoms.pdf", "Symptom")
            for fm in item.failure_modes:
                provenance[fm.failure_mode_id] = self._prov(
                    "FMEA", fm.failure_mode_id, f"fmea/{pid}/{fm.failure_mode_id}.pdf", "FailureMode"
                )
            for ds in item.diagnostic_steps:
                provenance[ds.step_id] = self._prov(
                    "ServiceManual",
                    ds.step_id,
                    f"manuals/{pid}/troubleshooting.pdf#step={ds.order}",
                    "DiagnosticStep",
                )
            for pt in item.parts:
                provenance[pt.part_id] = self._prov("PIM", pt.part_number, f"pim/bom/{pid}", "Part")
            for res in item.historical_resolutions:
                provenance[res.resolution_id] = self._prov(
                    "FSM", res.resolution_id, f"fsm/resolutions/{res.resolution_id}", "HistoricalResolution"
                )

        from graph.warranty_catalog_extensions import build_enterprise_catalog_payload

        products = [p.model_dump() for p in graph_data.products]
        payload = build_enterprise_catalog_payload(products)
        payload["etl_batch_id"] = self.etl_batch_id
        payload["provenance"] = provenance
        return payload

    def _prov(self, system: str, record_id: str, doc_uri: str, entity_label: str) -> dict[str, Any]:
        defaults = self._manifest.get("entity_defaults", {}).get(entity_label, {})
        base = default_provenance(system, record_id, document_uri=doc_uri, batch_id=self.etl_batch_id)
        base.update({k: v for k, v in defaults.items() if k not in base})
        return base

    def _transform_product(
        self,
        pim_product: dict[str, Any],
        fsm_records: list[dict[str, Any]],
        claim_records: list[dict[str, Any]],
    ) -> ProductKnowledge:
        product = Product(**pim_product["product"])
        product_id = product.product_id
        return ProductKnowledge(
            product=product,
            symptoms=[Symptom(**s) for s in pim_product.get("symptoms", [])],
            failure_modes=[FailureMode(**fm) for fm in pim_product.get("failure_modes", [])],
            diagnostic_steps=[DiagnosticStep(**ds) for ds in pim_product.get("diagnostic_steps", [])],
            parts=[Part(**p) for p in pim_product.get("parts", [])],
            symptom_failure_links=self._build_symptom_links(
                pim_product.get("symptom_failure_links", []),
                product_id,
                fsm_records,
                claim_records,
            ),
            historical_resolutions=self._merge_resolutions(
                pim_product.get("historical_resolutions", []),
                product_id,
                fsm_records,
                claim_records,
            ),
            failure_mode_part_links=[
                FailureModePartLink(**link) for link in pim_product.get("failure_mode_part_links", [])
            ],
        )

    def _build_symptom_links(
        self,
        pim_links: list[dict[str, Any]],
        product_id: str,
        fsm_records: list[dict[str, Any]],
        claim_records: list[dict[str, Any]],
    ) -> list[SymptomFailureLink]:
        confidence_map: dict[tuple[str, str], float] = {
            (link["symptom_id"], link["failure_mode_id"]): float(link["confidence"]) for link in pim_links
        }
        for record in fsm_records + claim_records:
            if record.get("product_id") != product_id:
                continue
            key = (record.get("symptom_id"), record.get("confirmed_failure_mode_id"))
            if not key[0] or not key[1]:
                continue
            confidence_map[key] = min(0.99, round(confidence_map.get(key, 0.5) + 0.02, 2))
        return [
            SymptomFailureLink(symptom_id=k[0], failure_mode_id=k[1], confidence=v)
            for k, v in sorted(confidence_map.items())
        ]

    def _merge_resolutions(
        self,
        pim_resolutions: list[dict[str, Any]],
        product_id: str,
        fsm_records: list[dict[str, Any]],
        claim_records: list[dict[str, Any]],
    ) -> list[HistoricalResolution]:
        seen: set[str] = set()
        merged: list[HistoricalResolution] = []
        for item in pim_resolutions:
            res = HistoricalResolution(**item)
            merged.append(res)
            seen.add(res.resolution_id)
        for record in fsm_records:
            if record.get("product_id") != product_id:
                continue
            rid = record.get("work_order_id") or record.get("resolution_id")
            if not rid or rid in seen:
                continue
            merged.append(
                HistoricalResolution(
                    resolution_id=str(rid),
                    description=record.get("resolution_summary", "Field repair completed."),
                    confirmed_failure_mode_id=record["confirmed_failure_mode_id"],
                    resolution_date=record.get("closed_date", "2026-01-01"),
                    technician_notes=record.get("technician_notes", ""),
                )
            )
            seen.add(str(rid))
        for record in claim_records:
            if record.get("product_id") != product_id:
                continue
            rid = record.get("claim_id")
            if not rid or rid in seen:
                continue
            merged.append(
                HistoricalResolution(
                    resolution_id=str(rid),
                    description=record.get("resolution_summary", "Claim resolved."),
                    confirmed_failure_mode_id=record["confirmed_failure_mode_id"],
                    resolution_date=record.get("closed_date", "2026-01-01"),
                    technician_notes=record.get("agent_notes", ""),
                )
            )
            seen.add(str(rid))
        return merged
