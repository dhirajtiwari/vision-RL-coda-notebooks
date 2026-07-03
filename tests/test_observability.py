"""Tests for observability: PII redaction + metrics + gateway registry."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from observability.redaction import redact, redact_mapping


class TestRedaction:
    def test_email_redacted(self):
        assert "[EMAIL]" in redact("mail me at a.b@example.com now")

    def test_customer_id_redacted(self):
        assert "[CUSTOMER_ID]" in redact("case for CUST-99AB")

    def test_asset_id_redacted(self):
        assert "[ASSET_ID]" in redact("ASSET-7788 failed")

    def test_mapping_masks_sensitive_keys(self):
        out = redact_mapping({"customer_id": "CUST-1", "note": "ok"})
        assert out["customer_id"] == "[REDACTED]"
        assert out["note"] == "ok"

    def test_mapping_nested(self):
        out = redact_mapping({"a": {"email": "x@y.com", "b": "email z@w.com"}})
        assert out["a"]["email"] == "[REDACTED]"
        assert "[EMAIL]" in out["a"]["b"]

    def test_empty_string(self):
        assert redact("") == ""


class TestMetrics:
    def test_render_metrics_returns_bytes(self):
        from observability.metrics import render_latest_metrics

        assert isinstance(render_latest_metrics(), bytes)

    def test_observe_does_not_raise(self):
        from observability.metrics import observe_diagnosis, observe_request

        observe_request("/diagnose", 200, 0.12)
        observe_diagnosis(0.8, escalated=False)
        observe_diagnosis(0.2, escalated=True, reason="low_confidence")


class TestGatewayRegistry:
    def test_registry_loads_and_pins(self):
        from gateway.registry import load_registry

        registry = load_registry()
        # registry.yaml ships with the diagnosis-rewriter alias pinned.
        binding = registry.resolve("diagnosis-rewriter")
        assert not binding.model.endswith("latest")
        assert binding.provider in ("openai", "azure_foundry")

    def test_unknown_alias_raises(self):
        from gateway.registry import load_registry

        with pytest.raises(KeyError):
            load_registry().resolve("does-not-exist")

    def test_gateway_inactive_by_default(self):
        from gateway.router import GatewayError, ModelGateway

        gw = ModelGateway(enabled=False)
        with pytest.raises(GatewayError):
            gw.complete("diagnosis-rewriter", "hi")


class TestBudget:
    def test_circuit_breaker_trips(self):
        from finops.budget import BudgetExceeded, DailyCostBudget

        budget = DailyCostBudget(ceiling_usd=1.0)
        budget.check()  # ok
        budget.record(1.5)
        with pytest.raises(BudgetExceeded):
            budget.check()
