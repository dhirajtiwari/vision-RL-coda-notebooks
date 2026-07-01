"""Runtime health and configuration status for enterprise connectors."""

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
            "mode": "mock" if settings.use_mock_enterprise_apis else "live",
            "detail": str(exc)[:80],
        }


def integration_status() -> dict[str, Any]:
    from graph.neo4j_client import verify_connection

    neo4j_ok = verify_connection()
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
        "neo4j": {
            "configured": True,
            "reachable": neo4j_ok,
            "mode": "live",
            "detail": settings.neo4j_uri,
        },
        "crm": _connector_row("CRM", settings.resolved_crm_url()),
        "pim": _connector_row("PIM", settings.resolved_pim_url()),
        "claims": _connector_row("Claims", settings.resolved_claims_url()),
        "fsm": _connector_row("FSM", settings.resolved_fsm_url()),
        "mock_api": mock,
    }

    return {
        "demo_mode": settings.demo_mode,
        "fixture_fallback": settings.effective_fixture_fallback,
        "hybrid_symptom_matching": settings.use_hybrid_symptom_matching,
        "persistence": str(settings.database_path),
        "connectors": connectors,
    }


def _connector_row(name: str, url: str | None) -> dict[str, Any]:
    if not url:
        return {"configured": False, "reachable": False, "mode": "disabled", "detail": f"{name} URL not set"}
    if settings.use_mock_enterprise_apis and settings.mock_enterprise_api_url in (url or ""):
        return {
            "configured": True,
            "reachable": _check_url(settings.mock_enterprise_api_url, "/health")["reachable"],
            "mode": "mock",
            "detail": url,
        }
    row = _check_url(url, "")
    row["mode"] = "production"
    row["detail"] = url
    return row
