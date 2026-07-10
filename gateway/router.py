"""
Gateway router (kickoff prompt §G, handbook ch07).

Single entry point for LLM calls: resolve alias → pick provider → apply timeout
+ retries → ordered fallback → meter tokens/cost (FinOps) → return text.

INACTIVE by default. ``ModelGateway.enabled`` is False unless ``LLM_ENABLED=true``
and a provider credential is configured. Calling ``.complete`` while disabled
raises :class:`GatewayError` so nothing silently hits a paid API.
"""

from __future__ import annotations

import logging

from gateway.providers import (
    AzureFoundryProvider,
    Completion,
    OpenAIProvider,
    Provider,
)
from gateway.registry import ModelRegistry, load_registry

logger = logging.getLogger("diagnostics.gateway")


class GatewayError(RuntimeError):
    pass


class ModelGateway:
    def __init__(
        self,
        *,
        enabled: bool = False,
        registry: ModelRegistry | None = None,
        providers: dict[str, Provider] | None = None,
        budget: object | None = None,
    ) -> None:
        self.enabled = enabled
        self._registry = registry or load_registry()
        self._providers = providers or {}
        self._budget = budget

    @classmethod
    def from_settings(cls, settings) -> ModelGateway:
        """Build a gateway from app settings. Providers are wired only when
        their credentials + LLM_ENABLED are present (otherwise inactive)."""
        from finops.budget import DailyCostBudget

        enabled = bool(getattr(settings, "llm_enabled", False))
        providers: dict[str, Provider] = {}
        if enabled:
            if getattr(settings, "openai_api_key", None):
                providers["openai"] = OpenAIProvider(settings.openai_api_key)
            if getattr(settings, "azure_openai_api_key", None) and getattr(settings, "azure_openai_endpoint", None):
                providers["azure_foundry"] = AzureFoundryProvider(
                    settings.azure_openai_api_key,
                    settings.azure_openai_endpoint,
                    getattr(settings, "azure_openai_api_version", "2024-10-21"),
                )
        return cls(
            enabled=enabled and bool(providers),
            providers=providers,
            budget=DailyCostBudget.from_settings(settings),
        )

    def complete(self, alias: str, prompt: str, *, max_retries: int = 2) -> Completion:
        if not self.enabled:
            raise GatewayError(
                "LLM gateway is inactive (LLM_ENABLED=false or no provider "
                "credentials). Core diagnosis is deterministic."
            )
        if self._budget is not None:
            try:
                self._budget.check()  # type: ignore[attr-defined]
            except Exception as exc:
                from finops.budget import BudgetExceeded

                if isinstance(exc, BudgetExceeded):
                    raise GatewayError(str(exc)) from exc
                raise
        binding = self._registry.resolve(alias)
        chain = [binding.provider]
        if binding.fallback:
            fb = self._registry.resolve(binding.fallback)
            chain.append(fb.provider)

        last_error: Exception | None = None
        for provider_name in chain:
            provider = self._providers.get(provider_name)
            if provider is None:
                continue
            for attempt in range(max_retries + 1):
                try:
                    completion = provider.complete(prompt, model=binding.model, max_tokens=binding.max_tokens)
                    self._meter(binding, completion)
                    return completion
                except Exception as exc:  # noqa: BLE001 - fallback across providers
                    last_error = exc
                    logger.warning(
                        "gateway call failed provider=%s attempt=%d: %s",
                        provider_name,
                        attempt,
                        exc,
                    )
        raise GatewayError(f"all providers failed for alias '{alias}'") from last_error

    def _meter(self, binding, completion: Completion) -> None:
        try:
            from observability.metrics import observe_llm_usage

            cost = (
                completion.input_tokens / 1000 * binding.input_cost_per_1k
                + completion.output_tokens / 1000 * binding.output_cost_per_1k
            )
            observe_llm_usage(
                provider=completion.provider,
                model=completion.model,
                input_tokens=completion.input_tokens,
                output_tokens=completion.output_tokens,
                cost_usd=cost,
            )
            if self._budget is not None:
                self._budget.record(cost)  # type: ignore[attr-defined]
        except Exception:  # pragma: no cover - metering must never break a call
            logger.debug("metering skipped", exc_info=True)
