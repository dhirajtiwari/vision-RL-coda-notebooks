"""Abstract connector contract for enterprise source systems."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ConnectorResult:
    """Normalized payload returned by any enterprise connector."""

    source: str
    records: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


class EnterpriseConnector(ABC):
    """Base class for CRM, Claims, PIM, FSM, and other source adapters."""

    source_name: str

    @abstractmethod
    def fetch(self) -> ConnectorResult:
        """Pull raw records from the upstream system."""

    def health_check(self) -> bool:
        result = self.fetch()
        return result.ok


def load_fixture(fixture_path: Path) -> dict[str, Any] | None:
    if fixture_path.exists():
        return json.loads(fixture_path.read_text(encoding="utf-8"))
    return None
