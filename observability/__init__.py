"""
Observability package (kickoff prompt §H, handbook ch08–09).

Provides:
- Structured JSON logging with request/correlation IDs.
- OpenTelemetry tracing setup (OTLP exporter, gen_ai.* + diagnosis.* attrs).
- Prometheus metrics (latency, request count, diagnosis confidence, escalations).

Everything is opt-in via environment flags so the local demo keeps working with
zero extra infrastructure. See config/settings.py for the flags.
"""

from observability.logging_setup import get_logger, setup_logging
from observability.metrics import (
    METRICS_CONTENT_TYPE,
    observe_diagnosis,
    observe_request,
    render_latest_metrics,
)
from observability.tracing import setup_tracing, span

__all__ = [
    "setup_logging",
    "get_logger",
    "setup_tracing",
    "span",
    "observe_request",
    "observe_diagnosis",
    "render_latest_metrics",
    "METRICS_CONTENT_TYPE",
]
