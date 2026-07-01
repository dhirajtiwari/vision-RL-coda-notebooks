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


if __name__ == "__main__":
    test_health_endpoint()
    test_integrations_status_endpoint()
    test_diagnose_requires_neo4j()
    print("PASS: API smoke")
