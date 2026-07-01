"""API smoke tests (requires running services or skip)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_health_endpoint():
    r = client.get("/health")
    assert r.status_code == 200
    assert "status" in r.json()


def test_integrations_status_endpoint():
    r = client.get("/integrations/status")
    assert r.status_code == 200
    body = r.json()
    assert "connectors" in body
    assert "neo4j" in body["connectors"]


def test_diagnose_requires_neo4j():
    r = client.post("/diagnose", json={"message": "washer won't spin"})
    assert r.status_code in (200, 503)


def test_admin_open_when_no_token_configured():
    import api.main as m

    original = m.settings.admin_api_token
    m.settings.admin_api_token = ""
    try:
        assert client.post("/admin/pipeline/dry-run-etl").status_code == 200
    finally:
        m.settings.admin_api_token = original


def test_admin_requires_token_when_configured():
    import api.main as m

    original = m.settings.admin_api_token
    m.settings.admin_api_token = "secret-test-token"
    try:
        assert client.post("/admin/pipeline/dry-run-etl").status_code == 401
        assert client.post("/admin/pipeline/dry-run-etl", headers={"X-Admin-Token": "wrong"}).status_code == 401
        assert (
            client.post("/admin/pipeline/dry-run-etl", headers={"X-Admin-Token": "secret-test-token"}).status_code
            == 200
        )
    finally:
        m.settings.admin_api_token = original


if __name__ == "__main__":
    test_health_endpoint()
    test_integrations_status_endpoint()
    test_diagnose_requires_neo4j()
    test_admin_open_when_no_token_configured()
    test_admin_requires_token_when_configured()
    print("PASS: API smoke")
