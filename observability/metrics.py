"""
Prometheus metrics (kickoff prompt §F/§H/§I, handbook ch09).

Uses ``prometheus_client`` when available; otherwise degrades to a no-op so the
demo runs without the dependency. Metrics deliberately reuse the SAME definitions
that back SLOs and canary gates (metric catalog, ch09):

- diagnostics_requests_total{route,status}
- diagnostics_request_latency_seconds{route}
- diagnostics_diagnosis_confidence (histogram)
- diagnostics_escalations_total{reason}
- diagnostics_llm_tokens_total{provider,model,direction}   (FinOps, inactive path)
- diagnostics_llm_cost_usd_total{provider,model}
"""

from __future__ import annotations

import logging

logger = logging.getLogger("diagnostics.observability.metrics")

METRICS_CONTENT_TYPE = "text/plain; version=0.0.4; charset=utf-8"

try:
    from prometheus_client import (
        CONTENT_TYPE_LATEST,
        Counter,
        Histogram,
        generate_latest,
    )

    _AVAILABLE = True
    METRICS_CONTENT_TYPE = CONTENT_TYPE_LATEST
except ImportError:  # pragma: no cover - optional dependency
    _AVAILABLE = False
    logger.info("prometheus_client not installed; metrics are a no-op")


if _AVAILABLE:
    _REQUESTS = Counter(
        "diagnostics_requests_total",
        "Total API requests",
        ["route", "status"],
    )
    _LATENCY = Histogram(
        "diagnostics_request_latency_seconds",
        "Request latency in seconds",
        ["route"],
        buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
    )
    _CONFIDENCE = Histogram(
        "diagnostics_diagnosis_confidence",
        "Diagnosis confidence score distribution",
        buckets=(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.65, 0.75, 0.85, 0.95, 1.0),
    )
    _ESCALATIONS = Counter(
        "diagnostics_escalations_total",
        "Escalations to human agents",
        ["reason"],
    )
    _LLM_TOKENS = Counter(
        "diagnostics_llm_tokens_total",
        "LLM tokens (optional LLM path)",
        ["provider", "model", "direction"],
    )
    _LLM_COST = Counter(
        "diagnostics_llm_cost_usd_total",
        "LLM cost in USD (optional LLM path)",
        ["provider", "model"],
    )


def observe_request(route: str, status: int, latency_seconds: float) -> None:
    if not _AVAILABLE:
        return
    _REQUESTS.labels(route=route, status=str(status)).inc()
    _LATENCY.labels(route=route).observe(latency_seconds)


def observe_diagnosis(confidence: float, *, escalated: bool, reason: str = "none") -> None:
    if not _AVAILABLE:
        return
    if confidence is not None:
        _CONFIDENCE.observe(float(confidence))
    if escalated:
        _ESCALATIONS.labels(reason=reason or "unspecified").inc()


def observe_llm_usage(*, provider: str, model: str, input_tokens: int, output_tokens: int, cost_usd: float) -> None:
    """FinOps hook for the (currently inactive) LLM path."""
    if not _AVAILABLE:
        return
    _LLM_TOKENS.labels(provider=provider, model=model, direction="input").inc(input_tokens)
    _LLM_TOKENS.labels(provider=provider, model=model, direction="output").inc(output_tokens)
    _LLM_COST.labels(provider=provider, model=model).inc(cost_usd)


def render_latest_metrics() -> bytes:
    if not _AVAILABLE:
        return b"# prometheus_client not installed\n"
    return generate_latest()
