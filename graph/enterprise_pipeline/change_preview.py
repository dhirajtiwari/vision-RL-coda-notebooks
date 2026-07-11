"""
Change-set preview: compare incoming sources / catalog vs live Neo4j graphs.

Used by Admin onboarding so operators see **new products** and **detail updates**
before smoke → approve → promote.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from config.settings import settings
from graph.neo4j_client import get_driver, neo4j_env, verify_connection
from runtime.partitioning import product_id_from_record

# Entity list keys inside a catalog product bundle (for size/diff signals).
_BUNDLE_LIST_KEYS = (
    "symptoms",
    "failure_modes",
    "diagnostic_steps",
    "parts",
    "components",
    "error_codes",
    "historical_resolutions",
    "skus",
)


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _product_core(bundle_or_product: dict[str, Any]) -> dict[str, Any]:
    """Normalize nested catalog rows `{product: {...}, symptoms: [...]}`."""
    if not isinstance(bundle_or_product, dict):
        return {}
    inner = bundle_or_product.get("product")
    if isinstance(inner, dict) and (inner.get("product_id") or product_id_from_record(bundle_or_product)):
        return inner
    return bundle_or_product


def summarize_catalog_product(bundle: dict[str, Any]) -> dict[str, Any]:
    core = _product_core(bundle)
    pid = core.get("product_id") or product_id_from_record(bundle) or ""
    entity_counts = {
        k: len(bundle.get(k) or []) if isinstance(bundle.get(k), list) else 0
        for k in _BUNDLE_LIST_KEYS
        if isinstance(bundle.get(k), list)
    }
    # Direct product-edge counts (aligned with Neo4j HAS_SYMPTOM / CAN_HAVE / …)
    edge_counts = {
        "symptoms": entity_counts.get("symptoms", 0),
        "failure_modes": entity_counts.get("failure_modes", 0),
        "diagnostic_steps": entity_counts.get("diagnostic_steps", 0),
        "components": entity_counts.get("components", 0),
        "error_codes": entity_counts.get("error_codes", 0),
    }
    return {
        "product_id": pid,
        "name": core.get("name") or "",
        "brand": core.get("brand") or core.get("oem") or "",
        "category": core.get("category") or core.get("family") or "",
        "model_year": core.get("model_year"),
        "bulletin_id": core.get("last_bulletin_id") or core.get("bulletin_id") or "",
        "bulletin_revision": core.get("bulletin_revision") or "",
        "entity_counts": entity_counts,
        "edge_counts": edge_counts,
        "entity_total": sum(entity_counts.values()),
        "edge_total": sum(edge_counts.values()),
    }


def load_catalog_products(path: Path | None = None) -> list[dict[str, Any]]:
    catalog_path = path or settings.enterprise_catalog_file
    if not catalog_path.exists():
        return []
    try:
        data = json.loads(catalog_path.read_text(encoding="utf-8"))
    except Exception:
        return []
    products = data.get("products") if isinstance(data, dict) else data
    if not isinstance(products, list):
        return []
    out: list[dict[str, Any]] = []
    for row in products:
        if isinstance(row, dict):
            s = summarize_catalog_product(row)
            if s.get("product_id"):
                out.append(s)
    return out


def load_pim_source_products() -> list[dict[str, Any]]:
    """Products visible in enterprise PIM fixtures (pre-fetch / source side)."""
    pim_path = settings.enterprise_sources_dir / "pim_catalog.json"
    if not pim_path.exists():
        return []
    try:
        data = json.loads(pim_path.read_text(encoding="utf-8"))
    except Exception:
        return []
    products = data.get("products") if isinstance(data, dict) else data
    if not isinstance(products, list):
        return []
    out: list[dict[str, Any]] = []
    for row in products:
        if isinstance(row, dict):
            s = summarize_catalog_product(row)
            if s.get("product_id"):
                out.append(s)
    return out


def _graph_products(env: str) -> tuple[list[dict[str, Any]], str | None]:
    """Return (products, error)."""
    try:
        if not verify_connection(env):  # type: ignore[arg-type]
            return [], f"neo4j {env} not connected"
        with neo4j_env(env):  # type: ignore[arg-type]
            driver = get_driver()
            with driver.session() as session:
                result = session.run(
                    """
                    MATCH (p:Product)
                    OPTIONAL MATCH (p)-[:HAS_SYMPTOM]->(s:Symptom)
                    OPTIONAL MATCH (p)-[:CAN_HAVE]->(fm:FailureMode)
                    OPTIONAL MATCH (p)-[:HAS_DIAGNOSTIC_STEP]->(ds:DiagnosticStep)
                    OPTIONAL MATCH (p)-[:HAS_COMPONENT]->(c:Component)
                    OPTIONAL MATCH (p)-[:HAS_ERROR_CODE]->(ec:ErrorCode)
                    WITH p,
                         count(DISTINCT s) AS symptoms,
                         count(DISTINCT fm) AS failure_modes,
                         count(DISTINCT ds) AS diagnostic_steps,
                         count(DISTINCT c) AS components,
                         count(DISTINCT ec) AS error_codes
                    RETURN p.product_id AS product_id,
                           p.name AS name,
                           p.category AS category,
                           p.brand AS brand,
                           p.model_year AS model_year,
                           p.last_bulletin_id AS last_bulletin_id,
                           p.bulletin_revision AS bulletin_revision,
                           symptoms, failure_modes, diagnostic_steps, components, error_codes,
                           symptoms + failure_modes + diagnostic_steps + components + error_codes AS linked_entities
                    ORDER BY p.product_id
                    """
                )
                rows = []
                for r in result:
                    edge = {
                        "symptoms": int(r["symptoms"] or 0),
                        "failure_modes": int(r["failure_modes"] or 0),
                        "diagnostic_steps": int(r["diagnostic_steps"] or 0),
                        "components": int(r["components"] or 0),
                        "error_codes": int(r["error_codes"] or 0),
                    }
                    rows.append(
                        {
                            "product_id": r["product_id"],
                            "name": r["name"] or "",
                            "category": r["category"] or "",
                            "brand": r["brand"] or "",
                            "model_year": r["model_year"],
                            "last_bulletin_id": r["last_bulletin_id"] or "",
                            "bulletin_revision": r["bulletin_revision"] or "",
                            "edge_counts": edge,
                            "linked_entities": int(r["linked_entities"] or 0),
                        }
                    )
                return rows, None
    except Exception as exc:
        return [], str(exc)


def _index_by_id(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for item in items:
        pid = item.get("product_id")
        if pid:
            out[str(pid)] = item
    return out


def _field_changes(before: dict[str, Any], after: dict[str, Any], fields: tuple[str, ...]) -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []
    for f in fields:
        b, a = before.get(f), after.get(f)
        # Normalize empty
        if b is None:
            b = ""
        if a is None:
            a = ""
        if str(b) != str(a) and (a != "" or b != ""):
            changes.append({"field": f, "from": b, "to": a})
    return changes


def diff_products(
    *,
    incoming: list[dict[str, Any]],
    live_graph: list[dict[str, Any]],
    compare_fields: tuple[str, ...] = ("name", "brand", "category", "model_year"),
) -> dict[str, Any]:
    """
    Diff incoming product summaries vs live graph products.

    - new: in incoming, not in graph
    - updated: same id, name/brand/category/model_year differ OR entity footprint grew
    - unchanged: same id and fields match
    - graph_only: in graph, not in incoming (orphans relative to this snapshot)
    """
    inc = _index_by_id(incoming)
    live = _index_by_id(live_graph)

    new_products: list[dict[str, Any]] = []
    updated_products: list[dict[str, Any]] = []
    unchanged: list[dict[str, Any]] = []
    graph_only: list[dict[str, Any]] = []

    for pid, row in sorted(inc.items()):
        if pid not in live:
            new_products.append({**row, "change": "new", "reason": "Not present in live Neo4j graph"})
            continue
        g = live[pid]
        field_diffs = _field_changes(g, row, compare_fields)
        # ABox growth: sources/catalog richer than live graph (OEM bulletins, new FMs, …)
        ent_after = int(row.get("edge_total") or row.get("entity_total") or 0)
        ent_before = int(g.get("linked_entities") or 0)
        entity_note = None
        src_edges = row.get("edge_counts") or {}
        live_edges = g.get("edge_counts") or {}
        for key in ("symptoms", "failure_modes", "diagnostic_steps", "components", "error_codes"):
            a = int(src_edges.get(key) or 0)
            b = int(live_edges.get(key) or 0)
            if a > b:
                field_diffs.append({"field": f"abox_{key}", "from": b, "to": a})
                entity_note = (
                    f"Source ABox has more {key.replace('_', ' ')} than live graph "
                    f"({b} → {a}) — typically OEM bulletin / tech resolution updates"
                )
        if ent_after > 0 and ent_before == 0:
            entity_note = "Catalog has full ontology; live graph product has no linked entities yet"
            field_diffs.append({"field": "entity_footprint", "from": ent_before, "to": ent_after})
        # Bulletin revision not yet on graph product props
        src_bull = str(row.get("bulletin_id") or "")
        live_bull = str(g.get("last_bulletin_id") or "")
        if src_bull and src_bull != live_bull:
            field_diffs.append({"field": "bulletin_id", "from": live_bull or "(none)", "to": src_bull})
            entity_note = entity_note or f"OEM bulletin pending promote: {src_bull}"

        if field_diffs:
            updated_products.append(
                {
                    **row,
                    "change": "updated",
                    "change_kind": "product_update",
                    "live": {
                        "name": g.get("name"),
                        "brand": g.get("brand"),
                        "category": g.get("category"),
                        "model_year": g.get("model_year"),
                        "linked_entities": g.get("linked_entities"),
                        "edge_counts": live_edges,
                        "last_bulletin_id": g.get("last_bulletin_id"),
                    },
                    "field_changes": field_diffs,
                    "reason": entity_note or "Product details differ from live graph",
                }
            )
        else:
            unchanged.append(
                {
                    **row,
                    "change": "unchanged",
                    "live_linked_entities": ent_before,
                }
            )

    for pid, g in sorted(live.items()):
        if pid not in inc:
            graph_only.append({**g, "change": "graph_only", "reason": "In live graph but not in this incoming set"})

    return {
        "summary": {
            "incoming_count": len(inc),
            "live_graph_count": len(live),
            "new_count": len(new_products),
            "updated_count": len(updated_products),
            "unchanged_count": len(unchanged),
            "graph_only_count": len(graph_only),
            "has_actionable_changes": bool(new_products or updated_products),
        },
        "new_products": new_products,
        "updated_products": updated_products,
        "unchanged_products": unchanged,
        "graph_only_products": graph_only,
    }


def _merge_product_summaries(*lists: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Union by product_id; later lists win (e.g. PIM over catalog)."""
    by_id: dict[str, dict[str, Any]] = {}
    for lst in lists:
        for row in lst or []:
            pid = row.get("product_id")
            if pid:
                by_id[str(pid)] = row
    return [by_id[k] for k in sorted(by_id.keys())]


def apply_product_selection(
    preview: dict[str, Any],
    selection: dict[str, bool] | None = None,
    *,
    default_select_new: bool = True,
    default_select_updated: bool = False,
) -> dict[str, Any]:
    """
    Attach per-product selection flags for Admin change-set control.

    - **new** products default selected (onboard candidates)
    - **updated** products default deselected (opt-in detail merges)
    Operator overrides persist in ``selection`` map ``{product_id: bool}``.
    """
    selection = dict(selection or {})
    diff = preview.get("diff_vs_production") or {}
    new_list = list(diff.get("new_products") or [])
    upd_list = list(diff.get("updated_products") or [])

    def _with_sel(rows: list[dict[str, Any]], change_type: str, default: bool) -> list[dict[str, Any]]:
        out = []
        for row in rows:
            pid = str(row.get("product_id") or "")
            selected = selection.get(pid, default)
            out.append(
                {
                    **row,
                    "change_type": change_type,
                    "change_kind": "new_product" if change_type == "new" else "product_update",
                    "selected": bool(selected),
                    "badge": "NEW PRODUCT" if change_type == "new" else "UPDATE EXISTING",
                }
            )
            if pid:
                selection[pid] = bool(selected)
        return out

    new_list = _with_sel(new_list, "new", default_select_new)
    upd_list = _with_sel(upd_list, "updated", default_select_updated)

    selected_new = [p for p in new_list if p.get("selected")]
    selected_upd = [p for p in upd_list if p.get("selected")]
    selected_ids = [p["product_id"] for p in selected_new + selected_upd if p.get("product_id")]

    diff = {
        **diff,
        "new_products": new_list,
        "updated_products": upd_list,
        "selection_summary": {
            "selected_new_count": len(selected_new),
            "selected_updated_count": len(selected_upd),
            "selected_total": len(selected_ids),
            "selected_product_ids": selected_ids,
            "default_select_new": default_select_new,
            "default_select_updated": default_select_updated,
            "note": (
                "Only selected products should be materialised/promoted. "
                "NEW = not in live graph; UPDATE = already in graph with different details."
            ),
        },
    }
    preview = {
        **preview,
        "diff_vs_production": diff,
        "product_selection": selection,
        "selected_product_ids": selected_ids,
        "selection_policy": {
            "default_select_new": default_select_new,
            "default_select_updated": default_select_updated,
        },
    }
    # Refresh headline with selection awareness
    s = diff.get("summary") or {}
    n, u = int(s.get("new_count") or 0), int(s.get("updated_count") or 0)
    unchanged = int(s.get("unchanged_count") or 0)
    sn, su = len(selected_new), len(selected_upd)
    if n or u:
        preview["headline"] = (
            f"{n} NEW ({sn} selected) · {u} pending UPDATE(s) ({su} selected)"
            + (f" · {unchanged} already in sync with production" if unchanged else "")
            + " vs production Neo4j."
        )
    elif unchanged:
        preview["headline"] = (
            f"All {unchanged} catalog product(s) already in sync with production Neo4j "
            "(prior promotes included). Nothing pending to select."
        )
    return preview


def build_change_preview(
    *,
    incoming_products: list[dict[str, Any]] | None = None,
    source_label: str = "catalog",
    include_pim_sources: bool = True,
    selection: dict[str, bool] | None = None,
    default_select_new: bool = True,
    default_select_updated: bool = False,
) -> dict[str, Any]:
    """
    Full preview payload for Admin UI.

    Prefer explicit ``incoming_products`` (e.g. dry-run ETL output). Otherwise
    union enterprise catalog + PIM fixtures so brand-new source products appear
    even before materialize.
    """
    catalog_products = load_catalog_products()
    pim_products = load_pim_source_products() if include_pim_sources else []

    if incoming_products is not None:
        incoming = incoming_products
        label = source_label
    else:
        # Catalog wins on id collision: promote MERGEs catalog → Neo4j, so fleet
        # pending work must reflect catalog vs production — not raw PIM shells that
        # still carry bulletin_id / inflated counts after a successful promote.
        # PIM-only products (not yet materialised) still appear via first list.
        incoming = _merge_product_summaries(pim_products, catalog_products)
        if catalog_products:
            label = "catalog+pim" if pim_products else "catalog"
        else:
            label = "pim_sources"

    prod_graph, prod_err = _graph_products("production")
    stg_graph, stg_err = _graph_products("staging")

    vs_production = diff_products(incoming=incoming, live_graph=prod_graph)
    vs_staging = diff_products(incoming=incoming, live_graph=stg_graph) if not stg_err else None

    # Source inventory style: products in PIM not yet in production graph
    pim_vs_prod = diff_products(incoming=pim_products, live_graph=prod_graph) if pim_products else None

    # Catalog-authoritative fleet stats (what promote would still need)
    catalog_vs_prod = diff_products(incoming=catalog_products, live_graph=prod_graph) if catalog_products else None

    preview = {
        "generated_at": _utc_now(),
        "source_label": label,
        "incoming_products": incoming,
        "catalog_products": catalog_products,
        "pim_source_products": pim_products,
        "live_graph": {
            "production": {"products": prod_graph, "error": prod_err, "count": len(prod_graph)},
            "staging": {"products": stg_graph, "error": stg_err, "count": len(stg_graph)},
        },
        "diff_vs_production": vs_production,
        "diff_vs_staging": vs_staging,
        "diff_pim_vs_production": pim_vs_prod,
        "diff_catalog_vs_production": catalog_vs_prod,
        "headline": _headline(vs_production),
        "fleet_note": (
            "UPDATE/NEW is a live fleet diff of enterprise catalog vs production Neo4j "
            "(not session history). Products fully promoted and matching production appear under "
            "unchanged / already-in-sync — they leave the UPDATE list on the next Fetch/Refresh."
        ),
    }
    return apply_product_selection(
        preview,
        selection,
        default_select_new=default_select_new,
        default_select_updated=default_select_updated,
    )


def _headline(diff: dict[str, Any]) -> str:
    s = diff.get("summary") or {}
    n, u = int(s.get("new_count") or 0), int(s.get("updated_count") or 0)
    unchanged = int(s.get("unchanged_count") or 0)
    if n == 0 and u == 0:
        return (
            "No new product IDs and no ABox growth vs production Neo4j "
            f"({unchanged} product(s) already in sync — including prior promotes). "
            "If you added OEM bulletins, re-scan sources or Refresh preview."
        )
    parts = []
    if n:
        parts.append(f"{n} NEW product{'s' if n != 1 else ''}")
    if u:
        parts.append(f"{u} still pending UPDATE(s) vs production")
    if unchanged:
        parts.append(f"{unchanged} already in sync")
    return " · ".join(parts) + " (catalog/sources vs production Neo4j)."


def catalog_products_from_etl_payload(catalog: dict[str, Any]) -> list[dict[str, Any]]:
    products = catalog.get("products") if isinstance(catalog, dict) else []
    if not isinstance(products, list):
        return []
    out: list[dict[str, Any]] = []
    for row in products:
        if isinstance(row, dict):
            s = summarize_catalog_product(row)
            if s.get("product_id"):
                out.append(s)
    return out


def journey_entry(step: str, action: str, summary: str, changes: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "ts": _utc_now(),
        "step": step,
        "action": action,
        "summary": summary,
        "changes": changes or {},
    }
