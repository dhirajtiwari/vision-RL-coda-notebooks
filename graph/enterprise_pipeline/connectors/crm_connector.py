"""CRM connector — customer assets, warranty registration, case history."""

from __future__ import annotations

from pathlib import Path

from config.settings import settings
from graph.enterprise_pipeline.connectors.base import ConnectorResult, EnterpriseConnector, load_fixture
from graph.enterprise_pipeline.http_client import get_json

DEFAULT_FIXTURE = settings.enterprise_sources_dir / "crm_assets.json"


class CRMConnector(EnterpriseConnector):
    source_name = "CRM"

    def __init__(self, fixture_path: Path | None = None, api_base_url: str | None = None):
        self.fixture_path = fixture_path or DEFAULT_FIXTURE
        self.api_base_url = api_base_url or settings.resolved_crm_url()

    def fetch(self) -> ConnectorResult:
        if self.api_base_url:
            try:
                payload = get_json(f"{self.api_base_url.rstrip('/')}/customers")
                assets: list[dict] = []
                for customer in payload.get("customers", []):
                    detail = get_json(f"{self.api_base_url.rstrip('/')}/customers/{customer['customer_id']}/assets")
                    assets.extend(detail.get("registered_assets", []))
                return ConnectorResult(
                    source=self.source_name,
                    records=assets,
                    metadata={"customers": payload.get("customers", []), "mode": "http"},
                )
            except ConnectionError:
                payload = load_fixture(self.fixture_path)
                if payload:
                    return ConnectorResult(
                        source=self.source_name,
                        records=payload.get("registered_assets", []),
                        metadata={"customers": payload.get("customers", []), "mode": "fixture_fallback"},
                    )

        payload = load_fixture(self.fixture_path)
        if not payload:
            return ConnectorResult(source=self.source_name, errors=[f"CRM fixture missing: {self.fixture_path}"])
        return ConnectorResult(
            source=self.source_name,
            records=payload.get("registered_assets", []),
            metadata={"customers": payload.get("customers", []), "mode": "fixture"},
        )
