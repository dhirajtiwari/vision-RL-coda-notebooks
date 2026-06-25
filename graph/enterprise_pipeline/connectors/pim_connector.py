"""PIM/PLM connector — product catalog, FMEA, service manual diagnostic trees."""

from __future__ import annotations

import json
from pathlib import Path

from config.settings import settings
from graph.enterprise_pipeline.connectors.base import ConnectorResult, EnterpriseConnector
from graph.enterprise_pipeline.http_client import get_json

DEFAULT_FIXTURE = settings.enterprise_sources_dir / "pim_catalog.json"


class PIMConnector(EnterpriseConnector):
    source_name = "PIM"

    def __init__(self, fixture_path: Path | None = None, api_base_url: str | None = None):
        self.fixture_path = fixture_path or DEFAULT_FIXTURE
        self.api_base_url = api_base_url or settings.resolved_pim_url()

    def fetch(self) -> ConnectorResult:
        if self.api_base_url:
            try:
                payload = get_json(f"{self.api_base_url.rstrip('/')}/products")
                return ConnectorResult(
                    source=self.source_name,
                    records=payload.get("products", []),
                    metadata={"source_system": payload.get("source_system", "PIM-API"), "mode": "http"},
                )
            except ConnectionError as exc:
                return ConnectorResult(source=self.source_name, errors=[str(exc)])

        if not self.fixture_path.exists():
            return ConnectorResult(source=self.source_name, errors=[f"PIM fixture missing: {self.fixture_path}"])

        payload = json.loads(self.fixture_path.read_text(encoding="utf-8"))
        return ConnectorResult(
            source=self.source_name,
            records=payload.get("products", []),
            metadata={"source_system": payload.get("source_system", "PIM"), "mode": "fixture"},
        )