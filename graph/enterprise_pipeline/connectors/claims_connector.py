"""Claims management connector — warranty policies and closed claim outcomes."""

from __future__ import annotations

from pathlib import Path

from config.settings import settings
from graph.enterprise_pipeline.connectors.base import ConnectorResult, EnterpriseConnector, load_fixture
from graph.enterprise_pipeline.http_client import get_json

DEFAULT_FIXTURE = settings.enterprise_sources_dir / "claims_history.json"


class ClaimsConnector(EnterpriseConnector):
    source_name = "Claims"

    def __init__(self, fixture_path: Path | None = None, api_base_url: str | None = None):
        self.fixture_path = fixture_path or DEFAULT_FIXTURE
        self.api_base_url = api_base_url or settings.resolved_claims_url()

    def fetch(self) -> ConnectorResult:
        if self.api_base_url:
            try:
                payload = get_json(f"{self.api_base_url.rstrip('/')}/closed")
                return ConnectorResult(
                    source=self.source_name,
                    records=payload.get("closed_claims", []),
                    metadata={
                        "warranty_policies": payload.get("warranty_policies", []),
                        "mode": "http",
                    },
                )
            except ConnectionError:
                payload = load_fixture(self.fixture_path)
                if payload:
                    return ConnectorResult(
                        source=self.source_name,
                        records=payload.get("closed_claims", []),
                        metadata={
                            "warranty_policies": payload.get("warranty_policies", []),
                            "mode": "fixture_fallback",
                        },
                    )

        payload = load_fixture(self.fixture_path)
        if not payload:
            return ConnectorResult(source=self.source_name, errors=[f"Claims fixture missing: {self.fixture_path}"])
        return ConnectorResult(
            source=self.source_name,
            records=payload.get("closed_claims", []),
            metadata={"warranty_policies": payload.get("warranty_policies", []), "mode": "fixture"},
        )
