"""
Model registry loader (kickoff prompt §G, handbook ch07).

Resolves app-facing ALIASES to PINNED provider model versions defined in
``models/registry.yaml``. Never returns "latest". Rollback = flip the alias in
YAML (no code deploy).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

_REGISTRY_PATH = Path(__file__).resolve().parent.parent / "models" / "registry.yaml"


@dataclass(frozen=True)
class ModelBinding:
    alias: str
    provider: str
    model: str  # PINNED version, e.g. "gpt-4o-2024-11-20"
    status: str  # active | canary | deprecated
    fallback: str | None = None
    max_tokens: int = 1024
    input_cost_per_1k: float = 0.0
    output_cost_per_1k: float = 0.0


class ModelRegistry:
    def __init__(self, bindings: dict[str, ModelBinding]) -> None:
        self._bindings = bindings

    def resolve(self, alias: str) -> ModelBinding:
        if alias not in self._bindings:
            raise KeyError(f"unknown model alias '{alias}'")
        binding = self._bindings[alias]
        if binding.model.endswith("latest"):
            raise ValueError(f"alias '{alias}' resolves to an unpinned 'latest' model — pin a version")
        return binding

    def aliases(self) -> list[str]:
        return list(self._bindings)


def load_registry(path: Path | None = None) -> ModelRegistry:
    """Load and validate ``models/registry.yaml``. Empty registry if absent."""
    path = path or _REGISTRY_PATH
    if not path.exists():
        return ModelRegistry({})
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("pyyaml is required to load models/registry.yaml") from exc

    raw: dict[str, Any] = yaml.safe_load(path.read_text()) or {}
    bindings: dict[str, ModelBinding] = {}
    for alias, spec in (raw.get("models") or {}).items():
        bindings[alias] = ModelBinding(
            alias=alias,
            provider=spec["provider"],
            model=spec["model"],
            status=spec.get("status", "active"),
            fallback=spec.get("fallback"),
            max_tokens=spec.get("max_tokens", 1024),
            input_cost_per_1k=spec.get("input_cost_per_1k", 0.0),
            output_cost_per_1k=spec.get("output_cost_per_1k", 0.0),
        )
    return ModelRegistry(bindings)
