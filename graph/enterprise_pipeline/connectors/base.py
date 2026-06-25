"""Abstract connector contract for enterprise source systems."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
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