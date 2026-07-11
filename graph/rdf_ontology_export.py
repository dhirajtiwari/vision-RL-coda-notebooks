"""
Export warranty-diagnosis ontology schema and catalog instances as RDF / OWL.

Serializations (stdlib only — no rdflib dependency):
  - Turtle (.ttl)
  - RDF/XML (.rdf / .owl)

Standards alignment (documentation + IRIs, not a full reasoner):
  - W3C RDF 1.1 Concepts  — https://www.w3.org/TR/rdf11-concepts/
  - W3C RDF Schema        — https://www.w3.org/TR/rdf-schema/
  - W3C OWL 2             — https://www.w3.org/TR/owl2-overview/
  - W3C PROV-O (optional properties on entities)

Usage:
  python -m graph.rdf_ontology_export
  python -m graph.rdf_ontology_export --catalog data/synthetic_diagnosis_data.json \\
      --out docs/ontology/warranty-diagnosis.ttl --format turtle
"""

from __future__ import annotations

import argparse
import json
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape as xml_escape

from config.settings import PROJECT_ROOT, settings

# Application ontology namespace (stable demo IRI — not a public registry).
WD = "https://example.org/warranty-diagnosis#"
WD_ONTOLOGY = "https://example.org/warranty-diagnosis/ontology"
RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
RDFS = "http://www.w3.org/2000/01/rdf-schema#"
OWL = "http://www.w3.org/2002/07/owl#"
XSD = "http://www.w3.org/2001/XMLSchema#"
PROV = "http://www.w3.org/ns/prov#"

# Neo4j label / relationship → OWL class / object property local names.
CLASSES: list[tuple[str, str]] = [
    ("Product", "A manufacturable product family / catalog product."),
    ("Model", "Engineering model under a product family."),
    ("SKU", "Sellable stock-keeping unit / revision of a model."),
    ("Asset", "Installed unit (serial) bound to a product/SKU."),
    ("Symptom", "Customer-observable or technician-observed symptom."),
    ("ErrorCode", "Device-reported diagnostic code."),
    ("FailureMode", "Diagnosed failure mode (FMEA-aligned)."),
    ("DiagnosticStep", "Troubleshooting or confirmation step."),
    ("Component", "BOM / subsystem component (product structure)."),
    ("Part", "Serviceable replacement part."),
    ("Claim", "Warranty claim with confirmed failure and parts used."),
    ("HistoricalResolution", "Closed field or claim resolution precedent."),
    ("WarrantyPolicy", "Coverage rules for parts/labor."),
]

# (local_name, domain, range, comment, neo4j_type)
OBJECT_PROPERTIES: list[tuple[str, str, str, str, str]] = [
    ("hasModel", "Product", "Model", "Product has engineering model.", "HAS_MODEL"),
    ("hasSku", "Product", "SKU", "Product has SKU.", "HAS_SKU"),
    ("modelHasSku", "Model", "SKU", "Model has SKU revision.", "HAS_SKU"),
    ("instanceOf", "Asset", "Product", "Installed asset is instance of product.", "INSTANCE_OF"),
    ("boundToSku", "Asset", "SKU", "Asset bound to SKU.", "BOUND_TO_SKU"),
    ("hasSymptom", "Product", "Symptom", "Product can present symptom.", "HAS_SYMPTOM"),
    ("hasErrorCode", "Product", "ErrorCode", "Product can raise error code.", "HAS_ERROR_CODE"),
    ("canHave", "Product", "FailureMode", "Product can exhibit failure mode.", "CAN_HAVE"),
    ("hasDiagnosticStep", "Product", "DiagnosticStep", "Product has diagnostic step.", "HAS_DIAGNOSTIC_STEP"),
    (
        "indicates",
        "Symptom",
        "FailureMode",
        "Symptom indicates failure mode (confidence on edge in graph).",
        "INDICATES",
    ),
    ("errorCodeIndicates", "ErrorCode", "FailureMode", "Error code indicates failure mode.", "INDICATES"),
    ("confirms", "DiagnosticStep", "FailureMode", "Step confirms failure mode.", "CONFIRMS"),
    ("rulesOut", "DiagnosticStep", "FailureMode", "Step rules out failure mode.", "RULES_OUT"),
    ("nextStep", "DiagnosticStep", "DiagnosticStep", "Diagnostic tree branch to next step.", "NEXT_STEP"),
    ("impactsComponent", "FailureMode", "Component", "Failure impacts BOM component.", "IMPACTS_COMPONENT"),
    ("realizedBy", "Component", "Part", "Component realized by service part.", "REALIZED_BY"),
    ("requiresPart", "FailureMode", "Part", "Failure requires replacement part.", "REQUIRES_PART"),
    ("compatibleWith", "SKU", "Part", "SKU compatible with part.", "COMPATIBLE_WITH"),
    ("confirmed", "Claim", "FailureMode", "Claim confirmed failure mode.", "CONFIRMED"),
    ("usedPart", "Claim", "Part", "Claim used part.", "USED_PART"),
    ("forProduct", "HistoricalResolution", "Product", "Resolution for product.", "FOR_PRODUCT"),
    ("resolutionConfirmed", "HistoricalResolution", "FailureMode", "Resolution confirmed FM.", "CONFIRMED"),
    ("coveredBy", "Asset", "WarrantyPolicy", "Asset covered by policy.", "COVERED_BY"),
]

DATATYPE_PROPERTIES: list[tuple[str, str, str, str]] = [
    ("productId", "Product", "xsd:string", "Stable product identifier."),
    ("name", "Product", "xsd:string", "Display name."),
    ("category", "Product", "xsd:string", "Product category."),
    ("brand", "Product", "xsd:string", "Brand."),
    ("symptomId", "Symptom", "xsd:string", "Symptom identifier."),
    ("description", "Symptom", "xsd:string", "Symptom text."),
    ("severity", "Symptom", "xsd:string", "low | medium | high | critical."),
    ("failureModeId", "FailureMode", "xsd:string", "Failure mode identifier."),
    ("confidence", "owl:Thing", "xsd:decimal", "Link confidence 0–1 (reified as datatype on instances)."),
    ("partNumber", "Part", "xsd:string", "OEM / service part number."),
    ("estimatedCostUsd", "Part", "xsd:decimal", "Estimated part cost."),
    ("subsystem", "Component", "xsd:string", "Subsystem label (product structure aspect)."),
]


def _local(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_\-]", "_", name)


def _iri(local: str) -> str:
    return f"{WD}{_local(local)}"


def _ttl_escape(value: str) -> str:
    return (
        value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
    )


def _xsd_type_uri(short: str) -> str:
    if short.startswith("xsd:"):
        return XSD + short.split(":", 1)[1]
    return short


# ---------------------------------------------------------------------------
# Schema (TBox)
# ---------------------------------------------------------------------------


def schema_triples_ttl() -> list[str]:
    """OWL TBox: classes and properties as Turtle statements (without prefixes)."""
    lines: list[str] = []
    lines.append(f"<{WD_ONTOLOGY}> a owl:Ontology ;")
    lines.append('  rdfs:label "Enterprise Warranty Diagnosis Ontology" ;')
    lines.append(
        '  rdfs:comment "Formal schema for product, symptom, failure mode, BOM component, '
        "parts, diagnostic steps, assets, and claims. Product structure (Component/Part) "
        "implements the industrial hierarchy aspect often called topology in ISO 14224 / "
        'IEC 81346 product-aspect terms — not a separate subsystem." ;'
    )
    lines.append('  owl:versionInfo "1.0.0" .')
    lines.append("")

    for cls, comment in CLASSES:
        lines.append(f"wd:{cls} a owl:Class ;")
        lines.append(f'  rdfs:label "{cls}" ;')
        lines.append(f'  rdfs:comment "{_ttl_escape(comment)}" .')
        lines.append("")

    for local, domain, rng, comment, neo4j in OBJECT_PROPERTIES:
        lines.append(f"wd:{local} a owl:ObjectProperty ;")
        lines.append(f"  rdfs:domain wd:{domain} ;")
        lines.append(f"  rdfs:range wd:{rng} ;")
        lines.append(f'  rdfs:label "{local}" ;')
        lines.append(f'  rdfs:comment "{_ttl_escape(comment)} Neo4j type: {neo4j}." .')
        lines.append("")

    for local, domain, rng, comment in DATATYPE_PROPERTIES:
        lines.append(f"wd:{local} a owl:DatatypeProperty ;")
        if domain != "owl:Thing":
            lines.append(f"  rdfs:domain wd:{domain} ;")
        lines.append(f"  rdfs:range {_xsd_type_uri(rng).replace(XSD, 'xsd:')} ;")
        lines.append(f'  rdfs:label "{local}" ;')
        lines.append(f'  rdfs:comment "{_ttl_escape(comment)}" .')
        lines.append("")

    return lines


def turtle_prefixes() -> str:
    return "\n".join(
        [
            f"@prefix wd: <{WD}> .",
            f"@prefix rdf: <{RDF}> .",
            f"@prefix rdfs: <{RDFS}> .",
            f"@prefix owl: <{OWL}> .",
            f"@prefix xsd: <{XSD}> .",
            f"@prefix prov: <{PROV}> .",
            "",
        ]
    )


# ---------------------------------------------------------------------------
# Instances (ABox) from catalog JSON
# ---------------------------------------------------------------------------


def _literal_ttl(value: Any, datatype: str | None = None) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int | float) and not isinstance(value, bool):
        if datatype:
            return f'"{value}"^^{datatype}'
        return str(value)
    s = _ttl_escape(str(value))
    if datatype:
        return f'"{s}"^^{datatype}'
    return f'"{s}"'


def instance_ttl_for_product(product_data: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    product = product_data["product"]
    pid = product["product_id"]
    p_iri = f"wd:product_{_local(pid)}"

    lines.append(f"{p_iri} a wd:Product ;")
    lines.append(f"  wd:productId {_literal_ttl(pid)} ;")
    lines.append(f"  wd:name {_literal_ttl(product.get('name', ''))} ;")
    lines.append(f"  wd:category {_literal_ttl(product.get('category', ''))} ;")
    lines.append(f"  wd:brand {_literal_ttl(product.get('brand', ''))} .")
    lines.append("")

    model = product_data.get("model")
    if model:
        mid = model["model_id"]
        m_iri = f"wd:model_{_local(mid)}"
        lines.append(f"{m_iri} a wd:Model ;")
        lines.append(f'  rdfs:label {_literal_ttl(model.get("name", mid))} ;')
        lines.append(f'  rdfs:comment {_literal_ttl(model.get("model_number", ""))} .')
        lines.append(f"{p_iri} wd:hasModel {m_iri} .")
        lines.append("")

    for sku in product_data.get("skus", []):
        sid = sku["sku_id"]
        s_iri = f"wd:sku_{_local(sid)}"
        lines.append(f"{s_iri} a wd:SKU ;")
        lines.append(f"  rdfs:label {_literal_ttl(sid)} .")
        lines.append(f"{p_iri} wd:hasSku {s_iri} .")
        if model:
            lines.append(f"wd:model_{_local(model['model_id'])} wd:modelHasSku {s_iri} .")
        lines.append("")

    for symptom in product_data.get("symptoms", []):
        sid = symptom["symptom_id"]
        s_iri = f"wd:symptom_{_local(sid)}"
        lines.append(f"{s_iri} a wd:Symptom ;")
        lines.append(f"  wd:symptomId {_literal_ttl(sid)} ;")
        lines.append(f"  wd:description {_literal_ttl(symptom.get('description', ''))} ;")
        lines.append(f"  wd:severity {_literal_ttl(symptom.get('severity', ''))} .")
        lines.append(f"{p_iri} wd:hasSymptom {s_iri} .")
        lines.append("")

    for fm in product_data.get("failure_modes", []):
        fid = fm["failure_mode_id"]
        f_iri = f"wd:fm_{_local(fid)}"
        lines.append(f"{f_iri} a wd:FailureMode ;")
        lines.append(f"  wd:failureModeId {_literal_ttl(fid)} ;")
        lines.append(f'  rdfs:label {_literal_ttl(fm.get("name", fid))} ;')
        lines.append(f'  rdfs:comment {_literal_ttl(fm.get("description", ""))} .')
        lines.append(f"{p_iri} wd:canHave {f_iri} .")
        lines.append("")

    for link in product_data.get("symptom_failure_links", []):
        conf = link.get("confidence", 0.0)
        lines.append(f"wd:symptom_{_local(link['symptom_id'])} wd:indicates wd:fm_{_local(link['failure_mode_id'])} .")
        # Annotate confidence on a reified blank node style statement as a parallel fact.
        lines.append(
            f"[] a owl:Axiom ; "
            f"owl:annotatedSource wd:symptom_{_local(link['symptom_id'])} ; "
            f"owl:annotatedProperty wd:indicates ; "
            f"owl:annotatedTarget wd:fm_{_local(link['failure_mode_id'])} ; "
            f"wd:confidence {_literal_ttl(conf, 'xsd:decimal')} ."
        )
        lines.append("")

    for step in product_data.get("diagnostic_steps", []):
        stid = step["step_id"]
        st_iri = f"wd:step_{_local(stid)}"
        lines.append(f"{st_iri} a wd:DiagnosticStep ;")
        lines.append(f"  rdfs:label {_literal_ttl(stid)} ;")
        lines.append(f'  rdfs:comment {_literal_ttl(step.get("description", ""))} .')
        lines.append(f"{p_iri} wd:hasDiagnosticStep {st_iri} .")
        lines.append("")

    for link in product_data.get("diagnostic_step_failure_links", []):
        prop = "confirms" if link.get("link_type", "CONFIRMS") == "CONFIRMS" else "rulesOut"
        lines.append(f"wd:step_{_local(link['step_id'])} wd:{prop} wd:fm_{_local(link['failure_mode_id'])} .")

    for tree in product_data.get("diagnostic_tree_links", []):
        lines.append(f"wd:step_{_local(tree['from_step_id'])} wd:nextStep wd:step_{_local(tree['to_step_id'])} .")

    for comp in product_data.get("components", []):
        cid = comp["component_id"]
        c_iri = f"wd:component_{_local(cid)}"
        lines.append(f"{c_iri} a wd:Component ;")
        lines.append(f'  rdfs:label {_literal_ttl(comp.get("name", cid))} ;')
        lines.append(f"  wd:subsystem {_literal_ttl(comp.get('subsystem', ''))} .")
        lines.append("")

    for part in product_data.get("parts", []):
        ptid = part["part_id"]
        pt_iri = f"wd:part_{_local(ptid)}"
        lines.append(f"{pt_iri} a wd:Part ;")
        lines.append(f'  rdfs:label {_literal_ttl(part.get("name", ptid))} ;')
        lines.append(f"  wd:partNumber {_literal_ttl(part.get('part_number', ''))} ;")
        cost = part.get("estimated_cost_usd", 0)
        lines.append(f"  wd:estimatedCostUsd {_literal_ttl(cost, 'xsd:decimal')} .")
        lines.append("")

    for link in product_data.get("failure_mode_component_links", []):
        lines.append(
            f"wd:fm_{_local(link['failure_mode_id'])} wd:impactsComponent "
            f"wd:component_{_local(link['component_id'])} ."
        )

    for link in product_data.get("component_part_links", []):
        lines.append(
            f"wd:component_{_local(link['component_id'])} wd:realizedBy " f"wd:part_{_local(link['part_id'])} ."
        )

    for link in product_data.get("failure_mode_part_links", []):
        lines.append(f"wd:fm_{_local(link['failure_mode_id'])} wd:requiresPart " f"wd:part_{_local(link['part_id'])} .")

    for link in product_data.get("sku_part_links", []):
        lines.append(f"wd:sku_{_local(link['sku_id'])} wd:compatibleWith " f"wd:part_{_local(link['part_id'])} .")

    for ec in product_data.get("error_codes", []):
        eid = ec["error_code_id"]
        e_iri = f"wd:ec_{_local(eid)}"
        lines.append(f"{e_iri} a wd:ErrorCode ;")
        lines.append(f'  rdfs:label {_literal_ttl(ec.get("code", eid))} ;')
        lines.append(f'  rdfs:comment {_literal_ttl(ec.get("description", ""))} .')
        lines.append(f"{p_iri} wd:hasErrorCode {e_iri} .")
        lines.append("")

    for link in product_data.get("error_code_failure_links", []):
        lines.append(
            f"wd:ec_{_local(link['error_code_id'])} wd:errorCodeIndicates " f"wd:fm_{_local(link['failure_mode_id'])} ."
        )

    return lines


def catalog_to_turtle(
    catalog: dict[str, Any],
    *,
    include_schema: bool = True,
    product_ids: Iterable[str] | None = None,
) -> str:
    """Serialize ontology schema and (optionally filtered) product instances to Turtle."""
    parts = [turtle_prefixes()]
    if include_schema:
        parts.append("\n".join(schema_triples_ttl()))
        parts.append("")

    wanted = set(product_ids) if product_ids else None
    for product_data in catalog.get("products", []):
        pid = product_data.get("product", {}).get("product_id")
        if wanted is not None and pid not in wanted:
            continue
        parts.append(f"# --- Product {pid} ---")
        parts.append("\n".join(instance_ttl_for_product(product_data)))
        parts.append("")

    for asset in catalog.get("assets", []):
        aid = asset["asset_id"]
        a_iri = f"wd:asset_{_local(aid)}"
        parts.append(f"{a_iri} a wd:Asset ;")
        parts.append(f'  rdfs:label {_literal_ttl(asset.get("serial_number", aid))} .')
        parts.append(f"{a_iri} wd:instanceOf wd:product_{_local(asset['product_id'])} .")
        if asset.get("sku_id"):
            parts.append(f"{a_iri} wd:boundToSku wd:sku_{_local(asset['sku_id'])} .")
        if asset.get("policy_id"):
            parts.append(f"{a_iri} wd:coveredBy wd:policy_{_local(asset['policy_id'])} .")
        parts.append("")

    for pol in catalog.get("warranty_policies", []):
        pid = pol["policy_id"]
        parts.append(f"wd:policy_{_local(pid)} a wd:WarrantyPolicy ;")
        parts.append(f'  rdfs:label {_literal_ttl(pol.get("description", pid))} .')
        parts.append("")

    for claim in catalog.get("claims", []):
        cid = claim["claim_id"]
        parts.append(f"wd:claim_{_local(cid)} a wd:Claim ;")
        parts.append(f"  rdfs:label {_literal_ttl(cid)} ;")
        parts.append(f'  rdfs:comment {_literal_ttl(claim.get("resolution_summary", ""))} .')
        if claim.get("confirmed_failure_mode_id"):
            parts.append(
                f"wd:claim_{_local(cid)} wd:confirmed " f"wd:fm_{_local(claim['confirmed_failure_mode_id'])} ."
            )
        if claim.get("used_part_id"):
            parts.append(f"wd:claim_{_local(cid)} wd:usedPart wd:part_{_local(claim['used_part_id'])} .")
        parts.append("")

    return "\n".join(parts).rstrip() + "\n"


def schema_only_turtle() -> str:
    return turtle_prefixes() + "\n".join(schema_triples_ttl()) + "\n"


# Neo4j label → OWL class local name (identity for UI / export)
NEO4J_LABEL_TO_OWL: dict[str, str] = {
    "Product": "Product",
    "Model": "Model",
    "SKU": "SKU",
    "Asset": "Asset",
    "Symptom": "Symptom",
    "ErrorCode": "ErrorCode",
    "FailureMode": "FailureMode",
    "DiagnosticStep": "DiagnosticStep",
    "Component": "Component",
    "Part": "Part",
    "Claim": "Claim",
    "HistoricalResolution": "HistoricalResolution",
    "Resolution": "HistoricalResolution",
    "WarrantyPolicy": "WarrantyPolicy",
}

# How instance IRIs are built for each class
_INSTANCE_IRI_PREFIX: dict[str, str] = {
    "Product": "product_",
    "Model": "model_",
    "SKU": "sku_",
    "Asset": "asset_",
    "Symptom": "symptom_",
    "ErrorCode": "ec_",
    "FailureMode": "fm_",
    "DiagnosticStep": "step_",
    "Component": "component_",
    "Part": "part_",
    "Claim": "claim_",
    "HistoricalResolution": "resolution_",
    "WarrantyPolicy": "policy_",
}


def owl_class_for_neo4j_label(label: str) -> str | None:
    return NEO4J_LABEL_TO_OWL.get(label) or NEO4J_LABEL_TO_OWL.get(label.replace(" ", ""))


def instance_iri_local(owl_class: str, entity_id: str) -> str:
    prefix = _INSTANCE_IRI_PREFIX.get(owl_class, f"{owl_class.lower()}_")
    return f"{prefix}{_local(entity_id)}"


def class_definition_ttl(owl_class: str) -> str:
    """
    W3C OWL TBox fragment for one class: owl:Class + related object/datatype properties
    (domain or range mentions this class).
    """
    lines: list[str] = [turtle_prefixes().rstrip(), ""]
    comment = next((c for n, c in CLASSES if n == owl_class), None)
    if not comment:
        return turtle_prefixes() + f"# Unknown OWL class: {owl_class}\n"

    lines.append(f"wd:{owl_class} a owl:Class ;")
    lines.append(f'  rdfs:label "{owl_class}" ;')
    lines.append(f'  rdfs:comment "{_ttl_escape(comment)}" .')
    lines.append("")
    lines.append(f"# Object properties with domain or range = {owl_class}")
    for local, domain, rng, prop_comment, neo4j in OBJECT_PROPERTIES:
        if domain != owl_class and rng != owl_class:
            continue
        lines.append(f"wd:{local} a owl:ObjectProperty ;")
        lines.append(f"  rdfs:domain wd:{domain} ;")
        lines.append(f"  rdfs:range wd:{rng} ;")
        lines.append(f'  rdfs:label "{local}" ;')
        lines.append(f'  rdfs:comment "{_ttl_escape(prop_comment)} Neo4j type: {neo4j}." .')
        lines.append("")
    lines.append(f"# Datatype properties with domain = {owl_class}")
    for local, domain, rng, prop_comment in DATATYPE_PROPERTIES:
        if domain != owl_class:
            continue
        lines.append(f"wd:{local} a owl:DatatypeProperty ;")
        lines.append(f"  rdfs:domain wd:{domain} ;")
        lines.append(f"  rdfs:range {_xsd_type_uri(rng).replace(XSD, 'xsd:')} ;")
        lines.append(f'  rdfs:label "{local}" ;')
        lines.append(f'  rdfs:comment "{_ttl_escape(prop_comment)}" .')
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _filter_ttl_for_entity(ttl_body: str, iri_local: str) -> str:
    """Keep Turtle lines that mention this instance (wd:product_… / etc.)."""
    token = f"wd:{iri_local}"
    keep: list[str] = []
    buf: list[str] = []
    for line in ttl_body.splitlines():
        if line.startswith("#"):
            if buf and any(token in x for x in buf):
                keep.extend(buf)
                keep.append("")
            buf = []
            continue
        if not line.strip():
            if buf and any(token in x for x in buf):
                keep.extend(buf)
                keep.append("")
            buf = []
            continue
        buf.append(line)
        # flush statement ending with .
        if line.rstrip().endswith("."):
            if any(token in x for x in buf):
                keep.extend(buf)
                keep.append("")
            buf = []
    if buf and any(token in x for x in buf):
        keep.extend(buf)
    return "\n".join(keep).rstrip() + ("\n" if keep else "")


def entity_instance_ttl(
    *,
    neo4j_label: str,
    entity_id: str,
    product_id: str | None = None,
    catalog: dict[str, Any] | None = None,
) -> str:
    """
    RDF ABox fragment for one individual: type assertion + properties + incident edges
    from the product catalog (and global assets/claims when relevant).
    """
    owl_class = owl_class_for_neo4j_label(neo4j_label)
    if not owl_class:
        return f"# No OWL mapping for Neo4j label {neo4j_label!r}\n"
    iri_local = instance_iri_local(owl_class, entity_id)
    catalog = catalog or load_catalog()
    parts: list[str] = [turtle_prefixes().rstrip(), ""]

    # Product-scoped entities: emit filtered product ABox
    product_ids: list[str] = []
    if product_id:
        product_ids = [product_id]
    else:
        # discover which products mention this entity
        for product_data in catalog.get("products", []):
            pid = product_data.get("product", {}).get("product_id")
            blob = json.dumps(product_data)
            if entity_id in blob and pid:
                product_ids.append(pid)
        if not product_ids and owl_class == "Product":
            product_ids = [entity_id]

    if product_ids:
        for pid in product_ids[:3]:
            for product_data in catalog.get("products", []):
                if product_data.get("product", {}).get("product_id") != pid:
                    continue
                body = "\n".join(instance_ttl_for_product(product_data))
                frag = _filter_ttl_for_entity(body, iri_local)
                if frag.strip():
                    parts.append(f"# --- From product {pid} ---")
                    parts.append(frag)
                break
    else:
        # Global catalog sections
        body_parts: list[str] = []
        for asset in catalog.get("assets", []):
            if asset.get("asset_id") == entity_id or owl_class == "Asset":
                aid = asset["asset_id"]
                if aid != entity_id and owl_class == "Asset":
                    continue
                if asset.get("asset_id") != entity_id:
                    continue
                a_iri = f"wd:asset_{_local(aid)}"
                body_parts.append(f"{a_iri} a wd:Asset ;")
                body_parts.append(f'  rdfs:label {_literal_ttl(asset.get("serial_number", aid))} .')
                body_parts.append(f"{a_iri} wd:instanceOf wd:product_{_local(asset['product_id'])} .")
        for pol in catalog.get("warranty_policies", []):
            if pol.get("policy_id") == entity_id:
                body_parts.append(f"wd:policy_{_local(entity_id)} a wd:WarrantyPolicy ;")
                body_parts.append(f'  rdfs:label {_literal_ttl(pol.get("description", entity_id))} .')
        if body_parts:
            parts.append("\n".join(body_parts))
        else:
            # Minimal type assertion if catalog has no detail
            parts.append(f"wd:{iri_local} a wd:{owl_class} ;")
            parts.append(f"  rdfs:label {_literal_ttl(entity_id)} ;")
            parts.append('  rdfs:comment "Individual present in Neo4j; limited catalog detail for RDF export." .')

    text = "\n".join(parts).rstrip() + "\n"
    if f"wd:{iri_local}" not in text and "a wd:" in text:
        return text
    if f"wd:{iri_local}" not in text:
        return (
            turtle_prefixes()
            + f"wd:{iri_local} a wd:{owl_class} ;\n"
            + f"  rdfs:label {_literal_ttl(entity_id)} ;\n"
            + f'  rdfs:comment "Mapped from Neo4j {neo4j_label}:{entity_id}." .\n'
        )
    return text


def describe_entity_rdf(
    *,
    neo4j_label: str,
    entity_id: str,
    product_id: str | None = None,
) -> dict[str, Any]:
    """
    API payload: complete OWL class definition + RDF instance triples for UI inspector.
    Aligns W3C RDF 1.1 / RDFS / OWL 2 purposes with Neo4j KG identity.
    """
    owl_class = owl_class_for_neo4j_label(neo4j_label)
    if not owl_class:
        return {
            "ok": False,
            "error": f"No OWL class mapping for Neo4j label {neo4j_label!r}",
            "neo4j_label": neo4j_label,
            "entity_id": entity_id,
        }
    iri_local = instance_iri_local(owl_class, entity_id)
    iri = _iri(iri_local)
    class_iri = _iri(owl_class)
    class_comment = next((c for n, c in CLASSES if n == owl_class), "")
    related_props = [
        {
            "name": local,
            "domain": domain,
            "range": rng,
            "neo4j": neo4j,
            "comment": comment,
        }
        for local, domain, rng, comment, neo4j in OBJECT_PROPERTIES
        if domain == owl_class or rng == owl_class
    ]
    return {
        "ok": True,
        "standards": {
            "rdf": "https://www.w3.org/TR/rdf11-concepts/",
            "rdfs": "https://www.w3.org/TR/rdf-schema/",
            "owl2": "https://www.w3.org/TR/owl2-overview/",
            "xsd": "https://www.w3.org/TR/xmlschema11-2/",
            "prov": "https://www.w3.org/TR/prov-o/",
        },
        "purposes": {
            "owl_tbox": "Formal vocabulary: classes and properties (what kinds of things exist).",
            "rdf_abox": "Ground facts as triples about this individual (what is true of this entity).",
            "knowledge_graph": "Runtime Neo4j property graph used for GraphRAG diagnosis and Explorer.",
        },
        "neo4j": {
            "label": neo4j_label,
            "entity_id": entity_id,
            "node_key": f"{neo4j_label}:{entity_id}",
        },
        "owl": {
            "class": owl_class,
            "class_iri": class_iri,
            "comment": class_comment,
            "related_properties": related_props,
        },
        "rdf": {
            "instance_iri": iri,
            "instance_curie": f"wd:{iri_local}",
            "namespace": WD,
        },
        "turtle": {
            "class_definition": class_definition_ttl(owl_class),
            "instance_definition": entity_instance_ttl(
                neo4j_label=neo4j_label,
                entity_id=entity_id,
                product_id=product_id,
            ),
            "combined": (
                class_definition_ttl(owl_class)
                + "\n# --- RDF ABox (this individual + incident edges) ---\n\n"
                + "\n".join(
                    line
                    for line in entity_instance_ttl(
                        neo4j_label=neo4j_label,
                        entity_id=entity_id,
                        product_id=product_id,
                    ).splitlines()
                    if not line.startswith("@prefix")
                )
                + "\n"
            ),
        },
        "product_id": product_id,
    }


def product_full_turtle(product_id: str, *, include_schema: bool = True) -> str:
    """Full diagram for one product: optional TBox + complete product ABox."""
    catalog = load_catalog()
    return catalog_to_turtle(catalog, include_schema=include_schema, product_ids=[product_id])


# ---------------------------------------------------------------------------
# RDF/XML (schema + minimal example individual)
# ---------------------------------------------------------------------------


def schema_to_rdfxml() -> str:
    """OWL/RDF-XML for the TBox (classes + properties)."""
    chunks: list[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<rdf:RDF xmlns:rdf="{RDF}"',
        f'         xmlns:rdfs="{RDFS}"',
        f'         xmlns:owl="{OWL}"',
        f'         xmlns:xsd="{XSD}"',
        f'         xmlns:wd="{WD}">',
        f'  <owl:Ontology rdf:about="{WD_ONTOLOGY}">',
        "    <rdfs:label>Enterprise Warranty Diagnosis Ontology</rdfs:label>",
        "    <owl:versionInfo>1.0.0</owl:versionInfo>",
        "  </owl:Ontology>",
    ]
    for cls, comment in CLASSES:
        chunks.append(f'  <owl:Class rdf:about="{_iri(cls)}">')
        chunks.append(f"    <rdfs:label>{xml_escape(cls)}</rdfs:label>")
        chunks.append(f"    <rdfs:comment>{xml_escape(comment)}</rdfs:comment>")
        chunks.append("  </owl:Class>")
    for local, domain, rng, comment, neo4j in OBJECT_PROPERTIES:
        chunks.append(f'  <owl:ObjectProperty rdf:about="{_iri(local)}">')
        chunks.append(f'    <rdfs:domain rdf:resource="{_iri(domain)}"/>')
        chunks.append(f'    <rdfs:range rdf:resource="{_iri(rng)}"/>')
        chunks.append(f"    <rdfs:comment>{xml_escape(comment)} Neo4j: {xml_escape(neo4j)}</rdfs:comment>")
        chunks.append("  </owl:ObjectProperty>")
    for local, domain, rng, comment in DATATYPE_PROPERTIES:
        chunks.append(f'  <owl:DatatypeProperty rdf:about="{_iri(local)}">')
        if domain != "owl:Thing":
            chunks.append(f'    <rdfs:domain rdf:resource="{_iri(domain)}"/>')
        chunks.append(f'    <rdfs:range rdf:resource="{_xsd_type_uri(rng)}"/>')
        chunks.append(f"    <rdfs:comment>{xml_escape(comment)}</rdfs:comment>")
        chunks.append("  </owl:DatatypeProperty>")
    # Tiny ABox example
    chunks.extend(
        [
            f'  <wd:Product rdf:about="{_iri("product_wm-001")}">',
            "    <wd:productId>wm-001</wd:productId>",
            "    <wd:name>AquaHome Front Load 8kg</wd:name>",
            f'    <wd:hasSymptom rdf:resource="{_iri("symptom_wm-s03")}"/>',
            f'    <wd:canHave rdf:resource="{_iri("fm_wm-fm02")}"/>',
            "  </wd:Product>",
            f'  <wd:Symptom rdf:about="{_iri("symptom_wm-s03")}">',
            "    <wd:description>Will not drain / E21</wd:description>",
            "    <wd:severity>high</wd:severity>",
            f'    <wd:indicates rdf:resource="{_iri("fm_wm-fm02")}"/>',
            "  </wd:Symptom>",
            f'  <wd:FailureMode rdf:about="{_iri("fm_wm-fm02")}">',
            "    <rdfs:label>Drain pump failure</rdfs:label>",
            f'    <wd:impactsComponent rdf:resource="{_iri("component_wm-c02")}"/>',
            f'    <wd:requiresPart rdf:resource="{_iri("part_wm-p02")}"/>',
            "  </wd:FailureMode>",
            f'  <wd:Component rdf:about="{_iri("component_wm-c02")}">',
            "    <rdfs:label>Drain System</rdfs:label>",
            "    <wd:subsystem>Plumbing</wd:subsystem>",
            f'    <wd:realizedBy rdf:resource="{_iri("part_wm-p02")}"/>',
            "  </wd:Component>",
            f'  <wd:Part rdf:about="{_iri("part_wm-p02")}">',
            "    <rdfs:label>Drain pump</rdfs:label>",
            "    <wd:partNumber>DP-8K-01</wd:partNumber>",
            "  </wd:Part>",
            "</rdf:RDF>",
        ]
    )
    return "\n".join(chunks) + "\n"


def load_catalog(path: Path | None = None) -> dict[str, Any]:
    catalog_path = path or settings.data_file
    if not catalog_path.exists():
        catalog_path = settings.enterprise_catalog_file
    if not catalog_path.exists():
        raise FileNotFoundError(f"No catalog found at {settings.data_file} or {settings.enterprise_catalog_file}")
    return json.loads(catalog_path.read_text(encoding="utf-8"))


def export_ontology(
    *,
    catalog_path: Path | None = None,
    out_path: Path,
    fmt: str = "turtle",
    include_schema: bool = True,
    product_ids: list[str] | None = None,
    schema_only: bool = False,
) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if fmt in ("rdfxml", "rdf", "owl"):
        out_path.write_text(schema_to_rdfxml(), encoding="utf-8")
        return out_path

    if schema_only:
        content = schema_only_turtle()
    else:
        catalog = load_catalog(catalog_path)
        content = catalog_to_turtle(
            catalog,
            include_schema=include_schema,
            product_ids=product_ids,
        )
    out_path.write_text(content, encoding="utf-8")
    return out_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export warranty diagnosis ontology as RDF/OWL")
    parser.add_argument(
        "--catalog",
        type=Path,
        default=None,
        help="Path to catalog JSON (default: settings.data_file)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=PROJECT_ROOT / "docs" / "ontology" / "warranty-diagnosis.ttl",
        help="Output file path",
    )
    parser.add_argument(
        "--format",
        choices=("turtle", "rdfxml"),
        default="turtle",
        help="Serialization format",
    )
    parser.add_argument(
        "--schema-only",
        action="store_true",
        help="Export TBox only (no catalog instances)",
    )
    parser.add_argument(
        "--product-id",
        action="append",
        dest="product_ids",
        help="Limit ABox to one or more product_ids (repeatable)",
    )
    args = parser.parse_args(argv)

    path = export_ontology(
        catalog_path=args.catalog,
        out_path=args.out,
        fmt=args.format,
        product_ids=args.product_ids,
        schema_only=args.schema_only,
    )
    print(f"Wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
