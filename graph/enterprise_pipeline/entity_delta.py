"""
Entity-level ABox deltas for Admin onboarding.

Answers: "what is actually NEW for mw-001?" — symptoms, failure modes,
diagnostic steps, parts — catalog vs live Neo4j (staging / production).
"""

from __future__ import annotations

import json
from typing import Any

from config.settings import settings
from graph.neo4j_client import get_driver, neo4j_env, verify_connection
from runtime.partitioning import product_id_from_record

# Catalog list key → (id field, display fields)
_ENTITY_SPECS: dict[str, tuple[str, tuple[str, ...]]] = {
    "symptoms": ("symptom_id", ("description", "severity")),
    "failure_modes": ("failure_mode_id", ("name", "description")),
    "diagnostic_steps": ("step_id", ("description", "expected_outcome", "order")),
    "parts": ("part_id", ("name", "part_number", "estimated_cost_usd")),
    "components": ("component_id", ("name", "subsystem")),
    "error_codes": ("error_code_id", ("code", "description")),
    "historical_resolutions": ("resolution_id", ("description", "resolution_date")),
}


def _product_core(bundle: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(bundle, dict):
        return {}
    inner = bundle.get("product")
    if isinstance(inner, dict) and (inner.get("product_id") or product_id_from_record(bundle)):
        return inner
    return bundle


def load_catalog_bundle(product_id: str) -> dict[str, Any] | None:
    path = settings.enterprise_catalog_file
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    products = data.get("products") if isinstance(data, dict) else data
    if not isinstance(products, list):
        return None
    want = str(product_id)
    for row in products:
        if not isinstance(row, dict):
            continue
        core = _product_core(row)
        pid = core.get("product_id") or product_id_from_record(row)
        if str(pid) == want:
            return row
    return None


def _catalog_entities(bundle: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for key, (id_field, display_fields) in _ENTITY_SPECS.items():
        rows: list[dict[str, Any]] = []
        for item in bundle.get(key) or []:
            if not isinstance(item, dict):
                continue
            eid = item.get(id_field)
            if not eid:
                continue
            row: dict[str, Any] = {
                "id": str(eid),
                "entity_type": key.rstrip("s") if key != "failure_modes" else "failure_mode",
            }
            row["entity_type"] = {
                "symptoms": "Symptom",
                "failure_modes": "FailureMode",
                "diagnostic_steps": "DiagnosticStep",
                "parts": "Part",
                "components": "Component",
                "error_codes": "ErrorCode",
                "historical_resolutions": "HistoricalResolution",
            }.get(key, key)
            for f in display_fields:
                if f in item and item[f] is not None:
                    row[f] = item[f]
            # Canonical label for UI
            row["label"] = item.get("name") or item.get("description") or item.get("code") or str(eid)
            rows.append(row)
        out[key] = rows
    return out


def _graph_entities(
    product_id: str,
    env: str,
    *,
    known_part_ids: list[str] | None = None,
) -> tuple[dict[str, list[dict[str, Any]]], str | None]:
    """Load ABox entity ids/labels from Neo4j for one product.

    ``known_part_ids``: when provided (from catalog), only those Part nodes are counted —
    avoids oem-* prefix matching hundreds of unrelated parts.
    """
    if env not in ("production", "staging"):
        return {}, f"invalid env {env}"
    try:
        if not verify_connection(env):  # type: ignore[arg-type]
            return {}, f"neo4j {env} not connected"
    except Exception as exc:
        return {}, str(exc)

    empty: dict[str, list[dict[str, Any]]] = {k: [] for k in _ENTITY_SPECS}
    try:
        with neo4j_env(env):  # type: ignore[arg-type]
            driver = get_driver()
            with driver.session() as session:
                # Product present?
                exists = session.run(
                    "MATCH (p:Product {product_id: $pid}) RETURN p.product_id AS id, p.name AS name, "
                    "p.last_bulletin_id AS bulletin LIMIT 1",
                    pid=product_id,
                ).single()
                if not exists:
                    return empty, None

                cypher = """
                MATCH (p:Product {product_id: $pid})
                OPTIONAL MATCH (p)-[:HAS_SYMPTOM]->(s:Symptom)
                WITH p, collect(DISTINCT {
                  id: s.symptom_id,
                  label: coalesce(s.description, s.symptom_id),
                  description: s.description,
                  severity: s.severity
                }) AS symptoms
                OPTIONAL MATCH (p)-[:CAN_HAVE]->(fm:FailureMode)
                WITH p, symptoms, collect(DISTINCT {
                  id: fm.failure_mode_id,
                  label: coalesce(fm.name, fm.failure_mode_id),
                  name: fm.name,
                  description: fm.description
                }) AS failure_modes
                OPTIONAL MATCH (p)-[:HAS_DIAGNOSTIC_STEP]->(ds:DiagnosticStep)
                WITH p, symptoms, failure_modes, collect(DISTINCT {
                  id: ds.step_id,
                  label: coalesce(ds.description, ds.step_id),
                  description: ds.description,
                  expected_outcome: ds.expected_outcome,
                  order: ds.order
                }) AS diagnostic_steps
                OPTIONAL MATCH (p)-[:HAS_COMPONENT]->(c:Component)
                WITH p, symptoms, failure_modes, diagnostic_steps, collect(DISTINCT {
                  id: c.component_id,
                  label: coalesce(c.name, c.component_id),
                  name: c.name,
                  subsystem: c.subsystem
                }) AS components
                OPTIONAL MATCH (p)-[:HAS_ERROR_CODE]->(ec:ErrorCode)
                WITH p, symptoms, failure_modes, diagnostic_steps, components, collect(DISTINCT {
                  id: ec.error_code_id,
                  label: coalesce(ec.code, ec.error_code_id),
                  code: ec.code,
                  description: ec.description
                }) AS error_codes
                RETURN symptoms, failure_modes, diagnostic_steps, components, error_codes
                """
                row = session.run(cypher, pid=product_id).single()
                if not row:
                    return empty, None

                def _clean(items: list) -> list[dict[str, Any]]:
                    out: list[dict[str, Any]] = []
                    seen: set[str] = set()
                    for it in items or []:
                        if not it or not it.get("id"):
                            continue
                        eid = str(it["id"])
                        if eid in seen:
                            continue
                        seen.add(eid)
                        cleaned = {k: v for k, v in dict(it).items() if v is not None}
                        cleaned["id"] = eid
                        out.append(cleaned)
                    return out

                # Parts: prefer exact catalog ids; never use short "oem-" prefix (matches whole fleet)
                parts: list[dict[str, Any]] = []
                ids = [str(x) for x in (known_part_ids or []) if x]
                if ids:
                    parts_rows = session.run(
                        """
                        MATCH (pt:Part)
                        WHERE pt.part_id IN $ids
                        RETURN pt.part_id AS id, pt.name AS name, pt.part_number AS part_number
                        """,
                        ids=ids,
                    )
                    parts = _clean(
                        [
                            {
                                "id": r["id"],
                                "label": r["name"] or r["id"],
                                "name": r["name"],
                                "part_number": r["part_number"],
                            }
                            for r in parts_rows
                        ]
                    )
                else:
                    # Fallback: parts whose id starts with full product_id (not first segment)
                    parts_rows = session.run(
                        """
                        MATCH (pt:Part)
                        WHERE pt.part_id STARTS WITH $pid_dash OR pt.part_id = $pid
                        RETURN pt.part_id AS id, pt.name AS name, pt.part_number AS part_number
                        """,
                        pid_dash=product_id + "-",
                        pid=product_id,
                    )
                    parts = _clean(
                        [
                            {
                                "id": r["id"],
                                "label": r["name"] or r["id"],
                                "name": r["name"],
                                "part_number": r["part_number"],
                            }
                            for r in parts_rows
                        ]
                    )
                return {
                    "symptoms": _clean(row["symptoms"]),
                    "failure_modes": _clean(row["failure_modes"]),
                    "diagnostic_steps": _clean(row["diagnostic_steps"]),
                    "parts": parts,
                    "components": _clean(row["components"]),
                    "error_codes": _clean(row["error_codes"]),
                    "historical_resolutions": [],
                }, None
    except Exception as exc:
        return empty, str(exc)


def _index(entities: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(e["id"]): e for e in entities if e.get("id")}


def _diff_lists(
    catalog_list: list[dict[str, Any]],
    graph_list: list[dict[str, Any]],
) -> dict[str, Any]:
    c_idx = _index(catalog_list)
    g_idx = _index(graph_list)
    added = [c_idx[i] for i in sorted(set(c_idx) - set(g_idx))]
    removed = [g_idx[i] for i in sorted(set(g_idx) - set(c_idx))]
    shared = sorted(set(c_idx) & set(g_idx))
    return {
        "added": added,
        "removed": removed,
        "shared_count": len(shared),
        "catalog_count": len(c_idx),
        "graph_count": len(g_idx),
        "added_count": len(added),
        "removed_count": len(removed),
    }


def compute_product_entity_delta(
    product_id: str,
    *,
    compare_env: str = "production",
) -> dict[str, Any]:
    """Full entity delta for one product: catalog vs Neo4j + presence on both envs."""
    pid = str(product_id)
    bundle = load_catalog_bundle(pid)
    core = _product_core(bundle) if bundle else {}
    cat_ents = _catalog_entities(bundle) if bundle else {k: [] for k in _ENTITY_SPECS}
    known_parts = [e["id"] for e in (cat_ents.get("parts") or []) if e.get("id")]

    prod_ents, prod_err = _graph_entities(pid, "production", known_part_ids=known_parts)
    stg_ents, stg_err = _graph_entities(pid, "staging", known_part_ids=known_parts)
    compare = prod_ents if compare_env == "production" else stg_ents
    compare_err = prod_err if compare_env == "production" else stg_err

    by_type: dict[str, Any] = {}
    total_added = 0
    total_removed = 0
    core_added = 0
    core_removed = 0
    human_lines: list[str] = []
    # Core ABox drives promote confidence; HRs are catalog-only often
    core_keys = ("symptoms", "failure_modes", "diagnostic_steps", "parts", "components", "error_codes")

    type_labels = {
        "symptoms": "Symptom",
        "failure_modes": "FailureMode",
        "diagnostic_steps": "DiagnosticStep",
        "parts": "Part",
        "components": "Component",
        "error_codes": "ErrorCode",
        "historical_resolutions": "HistoricalResolution",
    }

    for key in _ENTITY_SPECS:
        d = _diff_lists(cat_ents.get(key) or [], compare.get(key) or [])
        by_type[key] = d
        total_added += d["added_count"]
        total_removed += d["removed_count"]
        if key in core_keys:
            core_added += d["added_count"]
            core_removed += d["removed_count"]
        # Prefer listing core ABox first
        limit = 10 if key in core_keys else 3
        for a in d["added"][:limit]:
            human_lines.append(
                f"+ {type_labels.get(key, key)} `{a.get('id')}` — {a.get('label') or a.get('name') or a.get('description') or ''}"
            )
        for r in d["removed"][:3]:
            human_lines.append(f"− {type_labels.get(key, key)} `{r.get('id')}` — {r.get('label') or ''}")

    # Stable order: core lines first
    human_core = [h for h in human_lines if not h.startswith("+ Historical") and not h.startswith("− Historical")]
    human_hr = [h for h in human_lines if h.startswith("+ Historical") or h.startswith("− Historical")]
    human_lines = human_core + human_hr

    in_prod = _product_in_graph(pid, "production")
    _product_in_graph(pid, "staging")

    # Presence checks: core catalog IDs in each env (ignore historical_resolutions for fully_loaded)
    def _presence(env_ents: dict[str, list], env_name: str) -> dict[str, Any]:
        missing: list[str] = []
        for key in core_keys:
            cids = {e["id"] for e in (cat_ents.get(key) or [])}
            gids = {e["id"] for e in (env_ents.get(key) or [])}
            for i in sorted(cids - gids):
                missing.append(f"{type_labels.get(key, key)}:{i}")
        counts = {k: len(env_ents.get(k) or []) for k in core_keys}
        product_present = _product_in_graph(pid, env_name)
        return {
            "product_present": product_present,
            "counts": counts,
            "missing_catalog_ids": missing[:25],
            "fully_loaded": product_present and len(missing) == 0 and bool(bundle),
            "docker_hint": (
                "Neo4j Docker bolt " + (settings.neo4j_uri if env_name == "production" else settings.neo4j_staging_uri)
            ),
        }

    prod_presence = _presence(prod_ents, "production")
    stg_presence = _presence(stg_ents, "staging")

    if not bundle:
        change_kind = "missing_catalog"
        headline = f"{pid}: not in enterprise catalog"
    elif not in_prod and sum(len(cat_ents.get(k) or []) for k in core_keys) > 0:
        # Diff already treats all catalog entities as added when graph is empty
        change_kind = "new_product"
        headline = f"{pid}: NEW product — not in production Neo4j yet ({core_added} core ABox entities)"
    elif core_added > 0 and not prod_presence.get("fully_loaded"):
        # Pending work = catalog ahead of production (new ABox still missing on graph).
        change_kind = "product_update"
        bits = []
        for key in core_keys:
            n = by_type[key]["added_count"]
            if n:
                bits.append(f"+{n} {type_labels[key]}")
        headline = f"{pid}: pending UPDATE vs {compare_env} — " + (
            ", ".join(bits) if bits else f"{core_added} new core ABox entit(ies) in catalog"
        )
    elif core_added > 0 and prod_presence.get("fully_loaded"):
        # Edge-case race: counts looked different but all catalog ids present
        change_kind = "in_sync"
        headline = f"{pid}: in sync with production — all catalog ABox ids present on Neo4j"
    else:
        change_kind = "in_sync"
        hr_n = by_type.get("historical_resolutions", {}).get("added_count") or 0
        extra_graph = core_removed  # e.g. components on Neo4j not listed in catalog shell
        if hr_n and extra_graph:
            headline = (
                f"{pid}: in sync with {compare_env} (core ABox matches; "
                f"{hr_n} HR only in catalog; {extra_graph} graph-only edge(s) ignored)"
            )
        elif hr_n:
            headline = (
                f"{pid}: in sync with {compare_env} Neo4j "
                f"(core ABox matches; {hr_n} HistoricalResolution only in catalog)"
            )
        elif extra_graph:
            headline = (
                f"{pid}: in sync with {compare_env} Neo4j "
                f"(core ABox matches; {extra_graph} graph-only component/code edge(s) not in catalog)"
            )
        else:
            headline = f"{pid}: in sync with {compare_env} Neo4j (symptoms / FMs / steps / parts match)"

    bulletin_id = core.get("last_bulletin_id") or core.get("bulletin_id") or ""

    # Count table for UI: catalog | production | staging
    count_matrix = {}
    for key in core_keys:
        count_matrix[key] = {
            "catalog": len(cat_ents.get(key) or []),
            "production": len(prod_ents.get(key) or []),
            "staging": len(stg_ents.get(key) or []),
            "added_vs_compare": by_type[key]["added_count"],
        }

    return {
        "product_id": pid,
        "product_name": core.get("name") or "",
        "brand": core.get("brand") or "",
        "bulletin_id": bulletin_id,
        "change_kind": change_kind,
        "headline": headline,
        "compare_env": compare_env,
        "human_summary": human_lines[:30],
        "totals": {
            "added": total_added,
            "removed": total_removed,
            "core_added": core_added,
            "core_removed": core_removed,
            "catalog_entities": sum(len(v) for v in cat_ents.values()),
        },
        "by_type": by_type,
        "count_matrix": count_matrix,
        "catalog_counts": {k: len(cat_ents.get(k) or []) for k in _ENTITY_SPECS},
        "neo4j": {
            "production": {
                "uri": settings.neo4j_uri,
                "error": prod_err,
                **prod_presence,
            },
            "staging": {
                "uri": settings.neo4j_staging_uri,
                "error": stg_err,
                **stg_presence,
            },
        },
        "compare_error": compare_err,
        "rdf_hint": f"/graph/rdf/product/{pid}?include_schema=true",
        "explorer_hint": f"Knowledge Explorer → product {pid}",
        "how_to_verify": [
            f"Production Neo4j: {settings.neo4j_uri} (Docker neo4j / neo4j-demo)",
            f"Staging Neo4j: {settings.neo4j_staging_uri} (Docker neo4j-staging)",
            "Diagnosis Chat always reads production",
            f"RDF export: GET /graph/rdf/product/{pid}",
            f"Product graph: Knowledge Explorer product_id={pid}",
        ],
    }


def _product_in_graph(product_id: str, env: str) -> bool:
    try:
        if not verify_connection(env):  # type: ignore[arg-type]
            return False
        with neo4j_env(env):  # type: ignore[arg-type]
            driver = get_driver()
            with driver.session() as session:
                r = session.run(
                    "MATCH (p:Product {product_id: $pid}) RETURN 1 AS ok LIMIT 1",
                    pid=product_id,
                ).single()
                return bool(r)
    except Exception:
        return False


# How catalog entity types map onto OWL classes + Neo4j/RDF properties
_ONTOLOGY_MAP: dict[str, dict[str, str]] = {
    "symptoms": {
        "owl_class": "wd:Symptom",
        "product_property": "wd:hasSymptom",
        "neo4j_rel": "HAS_SYMPTOM",
        "iri_prefix": "wd:symptom_",
        "layer": "ABox",
    },
    "failure_modes": {
        "owl_class": "wd:FailureMode",
        "product_property": "wd:canHave",
        "neo4j_rel": "CAN_HAVE",
        "iri_prefix": "wd:fm_",
        "layer": "ABox",
    },
    "diagnostic_steps": {
        "owl_class": "wd:DiagnosticStep",
        "product_property": "wd:hasDiagnosticStep",
        "neo4j_rel": "HAS_DIAGNOSTIC_STEP",
        "iri_prefix": "wd:step_",
        "layer": "ABox",
    },
    "parts": {
        "owl_class": "wd:Part",
        "product_property": "wd:requiresPart (via FailureMode)",
        "neo4j_rel": "Part node (+ FM→Part links)",
        "iri_prefix": "wd:part_",
        "layer": "ABox",
    },
    "components": {
        "owl_class": "wd:Component",
        "product_property": "wd:impactsComponent",
        "neo4j_rel": "HAS_COMPONENT",
        "iri_prefix": "wd:component_",
        "layer": "ABox",
    },
    "error_codes": {
        "owl_class": "wd:ErrorCode",
        "product_property": "wd:hasErrorCode",
        "neo4j_rel": "HAS_ERROR_CODE",
        "iri_prefix": "wd:ec_",
        "layer": "ABox",
    },
}


def _local_id(raw: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in str(raw))


def _extract_turtle_blocks_for_ids(turtle: str, entity_ids: list[str]) -> list[dict[str, Any]]:
    """Pull contiguous Turtle statement groups that mention any of entity_ids."""
    if not turtle or not entity_ids:
        return []
    needles = [str(i) for i in entity_ids if i]
    lines = turtle.splitlines()
    # Split on blank lines into blocks
    blocks: list[list[str]] = []
    cur: list[str] = []
    for line in lines:
        if not line.strip():
            if cur:
                blocks.append(cur)
                cur = []
            continue
        cur.append(line)
    if cur:
        blocks.append(cur)

    out: list[dict[str, Any]] = []
    seen_text: set[str] = set()
    for block in blocks:
        text = "\n".join(block)
        hit = [n for n in needles if n in text]
        if not hit:
            continue
        if text in seen_text:
            continue
        seen_text.add(text)
        out.append({"entity_ids": hit, "turtle": text, "line_count": len(block)})
    return out


def build_ontology_rdf_highlight(product_id: str, delta: dict[str, Any]) -> dict[str, Any]:
    """
    Exact ontology + RDF locations for NEW ABox entities in a product delta.

    TBox (schema) is unchanged for bulletin UPDATEs — only ABox instances + edges grow.
    """
    from graph.rdf_ontology_export import product_full_turtle

    pid = str(product_id)
    by_type = delta.get("by_type") or {}
    new_ids: list[str] = []
    ontology_hits: list[dict[str, Any]] = []

    for key, meta in _ONTOLOGY_MAP.items():
        added = (by_type.get(key) or {}).get("added") or []
        for ent in added:
            eid = str(ent.get("id") or "")
            if not eid:
                continue
            new_ids.append(eid)
            local = _local_id(eid)
            iri = f"{meta['iri_prefix']}{local}"
            ontology_hits.append(
                {
                    "entity_id": eid,
                    "label": ent.get("label") or ent.get("name") or ent.get("description") or eid,
                    "catalog_type": key,
                    "layer": "ABox",  # never TBox for these bulletin deltas
                    "owl_class": meta["owl_class"],
                    "tbox_note": (
                        f"TBox class {meta['owl_class']} already exists — "
                        "no schema change; this is a new instance (ABox)."
                    ),
                    "product_link": {
                        "property": meta["product_property"],
                        "neo4j_rel": meta["neo4j_rel"],
                        "subject_iri": f"wd:product_{_local_id(pid)}",
                        "object_iri": iri,
                    },
                    "instance_iri": iri,
                    "highlight_tokens": [
                        eid,
                        iri,
                        meta["owl_class"].split(":")[-1],
                        meta["product_property"].split()[0],
                    ],
                }
            )

    full_abox = ""
    try:
        full_abox = product_full_turtle(pid, include_schema=False)
    except Exception as exc:
        full_abox = f"# RDF export failed: {exc}\n"

    turtle_blocks = _extract_turtle_blocks_for_ids(full_abox, new_ids)

    # Build a single NEW-only turtle document for UI
    new_only_lines = [
        "@prefix wd: <https://example.org/warranty-diagnosis#> .",
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .",
        "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .",
        "",
        f"# NEW ABox delta for {pid} (TBox schema unchanged)",
        f"# Entities: {', '.join(new_ids) if new_ids else '(none — in sync)'}",
        "",
    ]
    for b in turtle_blocks:
        new_only_lines.append(f"# --- NEW / related: {', '.join(b['entity_ids'])} ---")
        new_only_lines.append(b["turtle"])
        new_only_lines.append("")

    return {
        "product_id": pid,
        "tbox_changed": False,
        "tbox_summary": (
            "OWL classes (Symptom, FailureMode, DiagnosticStep, Part, …) and object properties "
            "(hasSymptom, canHave, hasDiagnosticStep, …) are shared TBox. This UPDATE only adds ABox instances."
        ),
        "abox_changed": bool(new_ids),
        "new_entity_ids": new_ids,
        "ontology_hits": ontology_hits,
        "turtle_new_only": "\n".join(new_only_lines),
        "turtle_blocks": turtle_blocks,
        "turtle_full_abox": full_abox,
        "how_to_read": [
            "Yellow/amber lines = NEW ABox (not yet on production Neo4j, or pending promote).",
            "TBox (class definitions at top of schema-only export) does not change for OEM bulletins.",
            f"Product IRI: wd:product_{_local_id(pid)}",
            "After production promote, the same triples exist as Neo4j nodes/relationships.",
        ],
    }


def _is_selection_actionable(delta: dict[str, Any]) -> bool:
    """True when materialize/promote still has work (not core-in-sync on production)."""
    kind = delta.get("change_kind")
    if kind in ("new_product", "product_update", "missing_catalog"):
        return True
    if kind == "in_sync":
        return False
    # Fallback: fully loaded production + no core adds → not actionable
    prod = (delta.get("neo4j") or {}).get("production") or {}
    core_added = int((delta.get("totals") or {}).get("core_added") or 0)
    # Fallback: fully loaded production + no core adds → not actionable
    return not (prod.get("fully_loaded") and core_added <= 0)


def build_selection_entity_deltas(
    product_ids: list[str],
    *,
    compare_env: str = "production",
    limit: int = 40,
    include_rdf: bool = True,
) -> dict[str, Any]:
    ids = [str(p) for p in product_ids if p][:limit]
    deltas = [compute_product_entity_delta(pid, compare_env=compare_env) for pid in ids]
    if include_rdf:
        for d in deltas:
            try:
                d["rdf_highlight"] = build_ontology_rdf_highlight(str(d.get("product_id") or ""), d)
            except Exception as exc:
                d["rdf_highlight"] = {
                    "error": str(exc),
                    "tbox_changed": False,
                    "abox_changed": False,
                    "ontology_hits": [],
                    "turtle_new_only": f"# RDF highlight failed: {exc}\n",
                }
    # Stable UI order: work first (pending / missing / new), then in-sync
    _kind_rank = {
        "new_product": 0,
        "product_update": 1,
        "missing_catalog": 2,
        "in_sync": 3,
    }
    deltas.sort(
        key=lambda d: (
            _kind_rank.get(str(d.get("change_kind") or ""), 9),
            str(d.get("product_id") or ""),
        )
    )
    total_added = sum(int((d.get("totals") or {}).get("core_added") or 0) for d in deltas)
    in_sync_ids = [
        str(d.get("product_id"))
        for d in deltas
        if d.get("change_kind") == "in_sync"
        or (
            ((d.get("neo4j") or {}).get("production") or {}).get("fully_loaded")
            and int((d.get("totals") or {}).get("core_added") or 0) <= 0
            and d.get("change_kind") not in ("new_product", "product_update", "missing_catalog")
        )
    ]
    actionable_ids = [str(d.get("product_id")) for d in deltas if _is_selection_actionable(d) and d.get("product_id")]
    missing_cat_ids = [str(d.get("product_id")) for d in deltas if d.get("change_kind") == "missing_catalog"]
    pending_ids = [
        str(d.get("product_id"))
        for d in deltas
        if d.get("change_kind") in ("product_update", "new_product") and d.get("product_id")
    ]
    all_in_sync = all(d.get("change_kind") == "in_sync" for d in deltas) if deltas else True
    prod_ok = all((d.get("neo4j") or {}).get("production", {}).get("fully_loaded") for d in deltas) if deltas else False
    stg_ok = all((d.get("neo4j") or {}).get("staging", {}).get("fully_loaded") for d in deltas) if deltas else False
    n_sync, n_act = len(in_sync_ids), len(actionable_ids)
    return {
        "compare_env": compare_env,
        "product_ids": ids,
        "products": deltas,
        "summary": {
            "product_count": len(deltas),
            "total_core_entities_added": total_added,
            "all_in_sync_with_compare_env": all_in_sync,
            "all_fully_loaded_production": prod_ok,
            "all_fully_loaded_staging": stg_ok,
            "in_sync_count": n_sync,
            "in_sync_product_ids": in_sync_ids,
            "actionable_count": n_act,
            "actionable_product_ids": actionable_ids,
            "pending_update_count": len(pending_ids),
            "pending_update_product_ids": pending_ids,
            "missing_catalog_count": len(missing_cat_ids),
            "missing_catalog_product_ids": missing_cat_ids,
            "headline": (
                f"{len(deltas)} selected · {n_act} need work · {n_sync} already IN SYNC"
                + (f" · {total_added} new core ABox entit(ies) vs {compare_env}" if total_added else "")
                if deltas
                else "No products in selection"
            ),
        },
    }
