"""Runtime health and configuration status for enterprise connectors + platform."""

from __future__ import annotations

from typing import Any

from config.settings import settings


def _check_url(url: str | None, path: str = "/health") -> dict[str, Any]:
    if not url:
        return {"configured": False, "reachable": False, "mode": "disabled"}
    try:
        from graph.enterprise_pipeline.http_client import get_json

        base = url.rstrip("/")
        health_url = base if path == "" else f"{base}{path}"
        if "/api/" in base and path == "/health":
            health_url = settings.mock_enterprise_api_url.rstrip("/") + "/health"
        payload = get_json(health_url)
        return {
            "configured": True,
            "reachable": True,
            "mode": "live" if not settings.use_mock_enterprise_apis else "mock",
            "detail": payload.get("status", "ok"),
        }
    except Exception as exc:
        return {
            "configured": True,
            "reachable": False,
            "mode": "fixture_fallback" if settings.effective_fixture_fallback else "unreachable",
            "detail": str(exc)[:120],
            "note": (
                "Using data/enterprise_sources fixtures (expected in local demo)"
                if settings.effective_fixture_fallback
                else "Live endpoint required"
            ),
        }


def _connector_row(name: str, url: str | None) -> dict[str, Any]:
    if not url:
        return {"configured": False, "reachable": False, "mode": "disabled", "detail": f"{name} URL not set"}
    if settings.use_mock_enterprise_apis and settings.mock_enterprise_api_url in (url or ""):
        mock_health = _check_url(settings.mock_enterprise_api_url, "/health")
        return {
            "configured": True,
            "reachable": mock_health.get("reachable", False),
            "mode": "fixture_fallback" if settings.effective_fixture_fallback else "mock",
            "detail": url,
            "note": (
                "Mock host down — ETL uses JSON fixtures under data/enterprise_sources/"
                if not mock_health.get("reachable") and settings.effective_fixture_fallback
                else None
            ),
        }
    row = _check_url(url, "")
    row["mode"] = "production"
    row["detail"] = url
    return row


def integration_status() -> dict[str, Any]:
    from graph.neo4j_client import neo4j_health, verify_connection
    from runtime.cache import cache_stats_snapshot
    from runtime.redis_client import redis_health

    neo4j_ok = verify_connection()
    nh = neo4j_health()
    redis = redis_health()
    mock = (
        _check_url(settings.mock_enterprise_api_url, "/health")
        if settings.use_mock_enterprise_apis
        else {
            "configured": False,
            "reachable": False,
            "mode": "disabled",
        }
    )

    connectors = {
        "neo4j_production": {
            "configured": True,
            "reachable": nh.get("production", {}).get("connected", neo4j_ok),
            "mode": "live",
            "detail": settings.neo4j_uri,
            "role": "diagnose + explorer read path",
        },
        "neo4j_staging": {
            "configured": bool(settings.neo4j_staging_uri),
            "reachable": nh.get("staging", {}).get("connected", False),
            "mode": "live" if not nh.get("staging", {}).get("same_as_production") else "same_as_production",
            "detail": settings.neo4j_staging_uri or settings.neo4j_uri,
            "role": "promote-first MERGE target",
        },
        "redis": {
            "configured": bool(settings.redis_url),
            "reachable": bool(redis.get("connected")),
            "mode": redis.get("mode", "memory"),
            "detail": settings.redis_url or "in-process memory",
            "role": "diagnose cache, rate limit, admission",
        },
        "crm": _connector_row("CRM", settings.resolved_crm_url()),
        "pim": _connector_row("PIM", settings.resolved_pim_url()),
        "claims": _connector_row("Claims", settings.resolved_claims_url()),
        "fsm": _connector_row("FSM", settings.resolved_fsm_url()),
        "mock_api": mock,
    }

    # KG control-plane inventory (best-effort)
    pipelines: list[dict[str, Any]] = []
    recent_runs: list[dict[str, Any]] = []
    try:
        from graph.enterprise_pipeline.control_plane import list_pipelines, list_runs

        pipelines = [
            {
                "id": p.id,
                "name": p.name,
                "source_kind": p.source_kind,
                "modes": list(p.supported_modes),
            }
            for p in list_pipelines()
        ]
        recent_runs = list_runs(limit=12)
    except Exception:
        pass

    return {
        "demo_mode": settings.demo_mode,
        "fixture_fallback": settings.effective_fixture_fallback,
        "hybrid_symptom_matching": settings.use_hybrid_symptom_matching,
        "strict_context_consistency": settings.strict_context_consistency,
        "enable_diagnose_cache": settings.enable_diagnose_cache,
        "cache_ttl_diagnose_seconds": settings.cache_ttl_diagnose_seconds,
        "provenance_enabled": settings.enable_provenance,
        "persistence": str(settings.database_path),
        "catalog": str(settings.enterprise_catalog_file),
        "pipeline_sources": str(settings.project_root / "data" / "pipeline_sources"),
        "neo4j_detail": nh,
        "redis": redis,
        "runtime_caches": cache_stats_snapshot(),
        "connectors": connectors,
        "kg_pipelines": pipelines,
        "kg_runs_recent": recent_runs,
        "capabilities": {
            "asset_first_diagnose": True,
            "dual_neo4j": True,
            "diagnose_read_cache": settings.enable_diagnose_cache,
            "kg_control_plane": True,
            "bulk_product_upsert": True,
            "warranty_asset_register": True,
            "rdf_owl_export": True,
            "rdf_owl_import_reasoner": False,
            "live_cdc_event_bus": False,
        },
        "ops_links": {
            "admin_control_room": "/admin (UI tab)",
            "kg_pipelines_api": "/admin/kg-pipelines",
            "bulk_products": "POST /admin/products/bulk-upsert",
            "register_warranty": "POST /admin/warranty/register-asset",
            "rdf_export_cli": "python -m graph.rdf_ontology_export",
            "health": "/health",
        },
    }
