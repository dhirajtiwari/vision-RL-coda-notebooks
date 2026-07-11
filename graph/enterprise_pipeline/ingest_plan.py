"""
Ingest plan: extract → detect diffs → recommend next actions.

After sources change and Fetch/diff runs, the control plane should answer:

  1. What changed? (new_product | product_update | tbox_extension | sources_changed)
  2. What checks are required?
  3. Which operator steps unlock next?

This is the recommendation layer on top of change_preview + ontology_validate.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from config.settings import settings
from graph.rdf_ontology_export import CLASSES

# Known catalog list keys that map to TBox classes (ABox lists)
_KNOWN_ABOX_LISTS = {
    "symptoms",
    "failure_modes",
    "diagnostic_steps",
    "parts",
    "components",
    "error_codes",
    "historical_resolutions",
    "skus",
    "claims",
    "models",  # often nested singular
}
_KNOWN_META = {
    "product",
    "model",
    "symptom_failure_links",
    "failure_mode_part_links",
    "failure_mode_component_links",
    "component_part_links",
    "error_code_failure_links",
    "diagnostic_step_failure_links",
    "sku_part_links",
    "diagnostic_tree_links",  # existing OEM packs — tree edges, not new TBox class
    "oem_sources",  # provenance metadata blob on OEM blueprints
    "catalog_metadata",
    "pipeline_ingest",
    "selection_filter",
    "etl_batch_id",
    "provenance",
    "products",
    "_test_pack",
}

_TBOX_CLASS_NAMES = {c[0] for c in CLASSES}


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def compute_sources_fingerprint(
    *,
    roots: list[Path] | None = None,
) -> dict[str, Any]:
    """
    Fingerprint pipeline + enterprise source files so we can recommend re-fetch
    when disk content changes since last plan.
    """
    project = Path(settings.project_root)
    default_roots = [
        project / "data" / "pipeline_sources",
        project / "data" / "enterprise_sources",
    ]
    scan_roots = roots or default_roots
    h = hashlib.sha256()
    file_count = 0
    total_bytes = 0
    latest_mtime = 0.0
    paths_sample: list[str] = []

    for root in scan_roots:
        if not root.exists():
            continue
        for p in sorted(root.rglob("*")):
            if not p.is_file() or p.name.startswith("."):
                continue
            try:
                st = p.stat()
            except OSError:
                continue
            rel = str(p.relative_to(project)) if str(p).startswith(str(project)) else str(p)
            h.update(rel.encode("utf-8", errors="ignore"))
            h.update(str(st.st_size).encode())
            h.update(str(int(st.st_mtime)).encode())
            file_count += 1
            total_bytes += st.st_size
            latest_mtime = max(latest_mtime, st.st_mtime)
            if len(paths_sample) < 40:
                paths_sample.append(rel)

    return {
        "fingerprint": h.hexdigest()[:32] if file_count else "empty",
        "file_count": file_count,
        "total_bytes": total_bytes,
        "latest_mtime": latest_mtime,
        "paths_sample": paths_sample,
        "generated_at": _utc_now(),
    }


def scan_tbox_extension_candidates(
    *,
    pim_path: Path | None = None,
) -> list[dict[str, Any]]:
    """
    Heuristic: unknown top-level keys on product bundles may signal new entity
    *types* (TBox extension needed). Does not auto-extend the ontology.
    """
    path = pim_path or (settings.enterprise_sources_dir / "pim_catalog.json")
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    products = data.get("products") if isinstance(data, dict) else data
    if not isinstance(products, list):
        return []

    unknown: dict[str, set[str]] = {}
    for row in products:
        if not isinstance(row, dict):
            continue
        prod = row.get("product") if isinstance(row.get("product"), dict) else row
        pid = str((prod or {}).get("product_id") or "?")
        for key in row:
            if key in _KNOWN_META or key in _KNOWN_ABOX_LISTS:
                continue
            if key.startswith("_"):
                continue
            # nested product fields are fine
            if key == "product":
                continue
            unknown.setdefault(key, set()).add(pid)

    out = []
    for key, pids in sorted(unknown.items()):
        # Guess a class-like name
        guess = key.rstrip("s").replace("_", " ").title().replace(" ", "")
        out.append(
            {
                "change_class": "tbox_extension",
                "unknown_key": key,
                "suggested_class_name": guess,
                "in_current_tbox": guess in _TBOX_CLASS_NAMES,
                "product_ids_sample": sorted(pids)[:12],
                "product_count": len(pids),
                "severity": "high" if guess not in _TBOX_CLASS_NAMES else "low",
                "reason": (
                    f"Source catalog uses list/object key '{key}' not mapped to domain TBox classes. "
                    "Governance review required before treating as ontology extension."
                ),
            }
        )
    return out


def _action(
    action_id: str,
    *,
    title: str,
    reason: str,
    priority: int,
    depends_on: list[str] | None = None,
    product_ids: list[str] | None = None,
    auto: bool = False,
    unlocks_step: int | None = None,
    blocking: bool = False,
    pipeline_id: str | None = None,
) -> dict[str, Any]:
    return {
        "action_id": action_id,
        "title": title,
        "reason": reason,
        "priority": priority,
        "depends_on": depends_on or [],
        "product_ids": product_ids or [],
        "auto": auto,
        "unlocks_wizard_step": unlocks_step,
        "blocking": blocking,
        "pipeline_id": pipeline_id,
        "status": "pending",
    }


def build_ingest_plan(
    *,
    change_preview: dict[str, Any] | None,
    product_selection: dict[str, bool] | None = None,
    selected_product_ids: list[str] | None = None,
    ontology_validation: dict[str, Any] | None = None,
    smoke_ok: bool = False,
    human_reviewed: bool = False,
    last_sources_fingerprint: str | None = None,
    materialize_done: bool = False,
    promote_done: bool = False,
    fetch_done: bool = False,
    tbox_review_acknowledged: bool = False,
) -> dict[str, Any]:
    """
    Build detected changes + ordered recommended actions for Admin.

    Wizard unlocks are derived from completed prerequisites + detection results.
    """
    preview = change_preview or {}
    diff = preview.get("diff_vs_production") or {}
    summary = diff.get("summary") or {}
    new_list = list(diff.get("new_products") or [])
    upd_list = list(diff.get("updated_products") or [])

    # Resolve selection
    sel_ids = list(selected_product_ids or preview.get("selected_product_ids") or [])
    if not sel_ids and product_selection:
        sel_ids = [str(k) for k, v in product_selection.items() if v]
    # Default recommendation scope: all actionable if nothing selected yet
    all_new_ids = [str(p.get("product_id")) for p in new_list if p.get("product_id")]
    all_upd_ids = [str(p.get("product_id")) for p in upd_list if p.get("product_id")]
    actionable_ids = all_new_ids + all_upd_ids

    fp = compute_sources_fingerprint()
    sources_changed = bool(
        last_sources_fingerprint and fp.get("fingerprint") and fp["fingerprint"] != last_sources_fingerprint
    )

    tbox_cands = scan_tbox_extension_candidates()
    high_tbox = [t for t in tbox_cands if t.get("severity") == "high"]

    detected = {
        "new_product": {
            "count": len(all_new_ids),
            "product_ids": all_new_ids,
            "items": [
                {
                    "product_id": p.get("product_id"),
                    "name": p.get("name"),
                    "change_class": "new_product",
                    "reason": p.get("reason") or "Not in live graph",
                }
                for p in new_list
            ],
        },
        "product_update": {
            "count": len(all_upd_ids),
            "product_ids": all_upd_ids,
            "items": [
                {
                    "product_id": p.get("product_id"),
                    "name": p.get("name"),
                    "change_class": "product_update",
                    "reason": p.get("reason"),
                    "field_changes": (p.get("field_changes") or [])[:8],
                    "bulletin_id": p.get("bulletin_id"),
                }
                for p in upd_list
            ],
        },
        "tbox_extension": {
            "count": len(high_tbox),
            "candidates": high_tbox,
            "note": (
                "TBox extensions are rare governance events. Normal OEM bulletins are ABox updates "
                "under existing classes (Symptom, FailureMode, …)."
            ),
        },
        "sources_fingerprint": fp,
        "sources_changed_since_last_plan": sources_changed,
        "summary": summary,
    }

    has_new = len(all_new_ids) > 0
    has_upd = len(all_upd_ids) > 0
    has_actionable = has_new or has_upd
    ont = ontology_validation or {}
    ont_ok = bool(ont.get("ok") or (ont.get("failed_count") == 0 and (ont.get("passed_count") or 0) > 0))
    ont_ran = bool(ont) and ("passed_count" in ont or "failed_count" in ont or "reports" in ont)

    actions: list[dict[str, Any]] = []

    # 0) Sources changed → re-fetch
    if sources_changed or not fetch_done:
        actions.append(
            _action(
                "fetch_preview",
                title="Fetch & preview (extract + diff)",
                reason=(
                    "Source files changed on disk — re-extract and re-diff vs live graph."
                    if sources_changed
                    else "No successful fetch in this session — extract sources and compute NEW/UPDATE delta."
                ),
                priority=1,
                unlocks_step=2,
                blocking=True,
                pipeline_id=None,
            )
        )

    # 1) TBox governance (if any) — advisory unless unacknowledged high candidates
    if high_tbox and not tbox_review_acknowledged:
        actions.append(
            _action(
                "review_tbox_extension",
                title="Review possible TBox extension (governance)",
                reason=(
                    f"{len(high_tbox)} unknown source key(s) not mapped to domain ontology classes. "
                    "Acknowledge after review to continue (or map keys into TBox)."
                ),
                priority=2,
                blocking=True,
                unlocks_step=None,
            )
        )
    elif high_tbox and tbox_review_acknowledged:
        actions.append(
            _action(
                "review_tbox_extension",
                title="TBox extension review acknowledged",
                reason=f"{len(high_tbox)} candidate(s) noted; operator acknowledged — ABox path continues.",
                priority=2,
            )
        )
        actions[-1]["status"] = "done"

    # 2) Select products
    if has_actionable and not sel_ids:
        actions.append(
            _action(
                "select_products",
                title="Select products for KG scope",
                reason=(
                    f"Detected {len(all_new_ids)} NEW and {len(all_upd_ids)} UPDATE product(s). "
                    "Choose which enter materialize/promote (never process all by accident)."
                ),
                priority=3,
                product_ids=actionable_ids,
                unlocks_step=3,
                blocking=True,
            )
        )
    elif has_actionable and sel_ids:
        actions.append(
            _action(
                "select_products",
                title="Selection set",
                reason=f"{len(sel_ids)} product(s) in scope: {', '.join(sel_ids[:12])}"
                + ("…" if len(sel_ids) > 12 else ""),
                priority=3,
                product_ids=sel_ids,
                unlocks_step=3,
                blocking=False,
            )
        )
        actions[-1]["status"] = "done"

    # 3) Validate ABox
    if has_actionable and sel_ids and not ont_ok:
        actions.append(
            _action(
                "validate_abox",
                title="Validate ABox against TBox shapes",
                reason=(
                    "Selection is set but ontology validation has not passed. "
                    "Required before materialize (fail-closed)."
                    if not ont_ran
                    else f"Validation failed for: {', '.join(ont.get('failed_product_ids') or []) or 'see report'}"
                ),
                priority=4,
                depends_on=["select_products"] if sel_ids else ["select_products"],
                product_ids=sel_ids,
                unlocks_step=4,
                blocking=True,
            )
        )
    elif has_actionable and sel_ids and ont_ok:
        actions.append(
            _action(
                "validate_abox",
                title="ABox validation passed",
                reason=ont.get("headline") or "Selected products conform to TBox shapes.",
                priority=4,
                product_ids=sel_ids,
                unlocks_step=4,
            )
        )
        actions[-1]["status"] = "done"

    # 4) Materialize
    if has_actionable and sel_ids and ont_ok and not materialize_done:
        actions.append(
            _action(
                "materialize",
                title="Materialize catalog (selection only)",
                reason="Upsert selected product ABox into enterprise catalog JSON.",
                priority=5,
                depends_on=["validate_abox"],
                product_ids=sel_ids,
                unlocks_step=5,
                blocking=True,
                pipeline_id="knowledge_materialize",
            )
        )
    elif materialize_done and sel_ids:
        actions.append(
            _action(
                "materialize",
                title="Catalog materialize done",
                reason="Selected products written to catalog (this session).",
                priority=5,
                product_ids=sel_ids,
                unlocks_step=5,
                pipeline_id="knowledge_materialize",
            )
        )
        actions[-1]["status"] = "done"

    # 5) Smoke
    if materialize_done and not smoke_ok:
        actions.append(
            _action(
                "smoke",
                title="Run smoke validation",
                reason="Catalog changed — run enterprise diagnosis scenarios before promote.",
                priority=6,
                depends_on=["materialize"],
                unlocks_step=6,
                blocking=True,
                pipeline_id="smoke_validate",
            )
        )
    elif smoke_ok:
        actions.append(
            _action(
                "smoke",
                title="Smoke passed",
                reason="Enterprise smoke scenarios OK.",
                priority=6,
                unlocks_step=6,
            )
        )
        actions[-1]["status"] = "done"

    # 6) Approve
    if smoke_ok and not human_reviewed:
        actions.append(
            _action(
                "approve",
                title="Human approve (change gate)",
                reason="Smoke passed — operator must approve before promote.",
                priority=7,
                depends_on=["smoke"],
                unlocks_step=7,
                blocking=True,
            )
        )
    elif human_reviewed:
        actions.append(
            _action(
                "approve",
                title="Approved",
                reason="Human review gate satisfied.",
                priority=7,
                unlocks_step=7,
            )
        )
        actions[-1]["status"] = "done"

    # 7) Promote
    if smoke_ok and human_reviewed and not promote_done and sel_ids:
        actions.append(
            _action(
                "promote",
                title="Promote selection to Neo4j",
                reason="MERGE selected products into staging then production.",
                priority=8,
                depends_on=["approve"],
                product_ids=sel_ids,
                unlocks_step=8,
                blocking=True,
                pipeline_id="promote_graph",
            )
        )
    elif promote_done:
        actions.append(
            _action(
                "promote",
                title="Promote complete",
                reason="Selection promoted — ready for customer persona tests.",
                priority=8,
                product_ids=sel_ids,
                unlocks_step=8,
            )
        )
        actions[-1]["status"] = "done"

    # No actionable delta
    if fetch_done and not has_actionable and not sources_changed and not high_tbox:
        actions.append(
            _action(
                "noop",
                title="No actionable product delta",
                reason="Sources match live graph IDs and ABox edge counts — nothing to materialize.",
                priority=9,
            )
        )
        actions[-1]["status"] = "done"

    actions.sort(key=lambda a: a["priority"])

    # Next action = first pending
    next_action = next((a for a in actions if a.get("status") != "done"), None)

    # Wizard unlocks: step N unlocked if prerequisites for that step satisfied
    tbox_blocks = bool(high_tbox) and not tbox_review_acknowledged
    unlocks = {
        1: True,  # sources always
        2: True,  # fetch always allowed
        3: fetch_done and has_actionable,  # select when there is something to pick
        4: fetch_done and bool(sel_ids) and has_actionable and not tbox_blocks,
        5: fetch_done and bool(sel_ids) and ont_ok and not tbox_blocks,
        6: materialize_done,
        7: smoke_ok,
        8: smoke_ok and human_reviewed and bool(sel_ids),
    }
    # If no delta, don't unlock select+
    if fetch_done and not has_actionable:
        unlocks[3] = False
        unlocks[4] = False
        unlocks[5] = False

    # Fail-closed materialize policy
    gates = {
        "allow_materialize": bool(sel_ids) and ont_ok and not tbox_blocks and has_actionable,
        "allow_promote": bool(sel_ids) and smoke_ok and human_reviewed,
        "require_validate_before_materialize": True,
        "block_reason": None,
        "tbox_review_required": tbox_blocks,
    }
    if tbox_blocks:
        gates["block_reason"] = "Acknowledge TBox-extension candidates in the plan (or resolve unknown source keys)"
        gates["allow_materialize"] = False
    elif has_actionable and not sel_ids:
        gates["block_reason"] = "Select at least one NEW or UPDATE product"
        gates["allow_materialize"] = False
    elif sel_ids and not ont_ok:
        gates["block_reason"] = "ABox validation must pass for selection before materialize"
        gates["allow_materialize"] = False

    headline_parts = []
    if sources_changed:
        headline_parts.append("sources changed on disk")
    if has_new:
        headline_parts.append(f"{len(all_new_ids)} NEW")
    if has_upd:
        headline_parts.append(f"{len(all_upd_ids)} UPDATE")
    if high_tbox:
        headline_parts.append(f"{len(high_tbox)} TBox-extension candidate(s)")
    if next_action:
        headline_parts.append(f"next: {next_action['title']}")

    return {
        "generated_at": _utc_now(),
        "headline": " · ".join(headline_parts) if headline_parts else "No pending ingest actions",
        "detected": detected,
        "recommended_actions": actions,
        "next_action": next_action,
        "wizard_unlocks": unlocks,
        "gates": gates,
        "scope": {
            "selected_product_ids": sel_ids,
            "actionable_product_ids": actionable_ids,
            "new_product_ids": all_new_ids,
            "updated_product_ids": all_upd_ids,
        },
        "policy": {
            "change_classes": ["new_product", "product_update", "tbox_extension", "sources_changed"],
            "tbox_note": "Domain TBox is shared; product packs are ABox. TBox extension is governance-only.",
            "fail_closed_materialize": True,
        },
    }
