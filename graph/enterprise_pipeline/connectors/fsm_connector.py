"""Field Service Management connector — technician work orders and confirmed repairs."""

from __future__ import annotations

import json
from pathlib import Path

from config.settings import settings
from graph.enterprise_pipeline.connectors.base import ConnectorResult, EnterpriseConnector
from graph.enterprise_pipeline.http_client import get_json

DEFAULT_FIXTURE = settings.enterprise_sources_dir / "fsm_work_orders.json"


class FSMConnector(EnterpriseConnector):
    source_name = "FSM"

    def __init__(self, fixture_path: Path | None = None, api_base_url: str | None = None):
        self.fixture_path = fixture_path or DEFAULT_FIXTURE
        self.api_base_url = api_base_url or settings.resolved_fsm_url()

    def fetch(self) -> ConnectorResult:
        if self.api_base_url:
            try:
                payload = get_json(f"{self.api_base_url.rstrip('/')}/work-orders?status=closed")
                return ConnectorResult(
                    source=self.source_name,
                    records=payload.get("closed_work_orders", []),
                    metadata={"mode": "http"},
                )
            except ConnectionError as exc:
                return ConnectorResult(source=self.source_name, errors=[str(exc)])

        if not self.fixture_path.exists():
            return ConnectorResult(source=self.source_name, errors=[f"FSM fixture missing: {self.fixture_path}"])

        payload = json.loads(self.fixture_path.read_text(encoding="utf-8"))
        return ConnectorResult(
            source=self.source_name,
            records=payload.get("closed_work_orders", []),
            metadata={"mode": "fixture"},
        )