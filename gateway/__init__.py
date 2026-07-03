"""
Model gateway (kickoff prompt §G, handbook ch07).

ALL LLM traffic — when the optional LLM path is enabled — routes through this
single control plane. Apps call model ALIASES (e.g. "diagnosis-rewriter"); the
alias resolves to a PINNED provider+version via ``models/registry.yaml`` (never
"latest"). Ordered fallback + retries + timeouts live here.

The core diagnosis is deterministic, so this gateway is INACTIVE by default
(``LLM_ENABLED=false``). It exists so activating the LLM later is a config flip,
not a re-architecture.
"""

from gateway.registry import ModelRegistry, load_registry
from gateway.router import GatewayError, ModelGateway

__all__ = ["ModelGateway", "GatewayError", "ModelRegistry", "load_registry"]
