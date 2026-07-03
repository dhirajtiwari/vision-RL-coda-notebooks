"""
OpenTelemetry tracing setup (kickoff prompt §H, handbook ch08).

Graceful-degradation design: if the ``opentelemetry`` packages are not installed
or ``OTEL_ENABLED=false``, :func:`span` becomes a no-op context manager and the
app runs exactly as before. When enabled, spans carry GenAI-aligned attributes
(``gen_ai.*``) plus diagnosis-specific attributes (``diagnosis.*``).

We keep OTel optional so the local Mac-mini demo needs no collector, while a real
deployment can flip ``OTEL_ENABLED=true`` and point at an OTLP endpoint.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

logger = logging.getLogger("diagnostics.observability.tracing")

_tracer: Any | None = None
_enabled = False


def setup_tracing(
    *,
    enabled: bool,
    service_name: str = "diagnostics-api",
    otlp_endpoint: str = "http://localhost:4317",
    sampler_ratio: float = 1.0,
) -> None:
    """Initialise the global tracer provider. Safe to call once at startup."""
    global _tracer, _enabled
    if not enabled:
        _enabled = False
        logger.info("OpenTelemetry tracing disabled (OTEL_ENABLED=false)")
        return
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.trace.sampling import (
            ParentBasedTraceIdRatio,
        )
    except ImportError:
        _enabled = False
        logger.warning(
            "OTEL_ENABLED=true but opentelemetry packages are not installed; "
            "tracing is a no-op. Install requirements to enable."
        )
        return

    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource, sampler=ParentBasedTraceIdRatio(sampler_ratio))
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)))
    trace.set_tracer_provider(provider)
    _tracer = trace.get_tracer("diagnostics")
    _enabled = True
    logger.info("OpenTelemetry tracing enabled → %s", otlp_endpoint)


def instrument_fastapi(app: Any) -> None:
    """Attach FastAPI auto-instrumentation when OTel is active."""
    if not _enabled:
        return
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        FastAPIInstrumentor.instrument_app(app)
    except ImportError:
        logger.debug("FastAPI OTel instrumentation not available")


@contextmanager
def span(name: str, **attributes: Any) -> Iterator[Any]:
    """Start a span with attributes. No-op when tracing is disabled.

    Usage:
        with span("diagnosis.run", **{"diagnosis.product_id": pid}) as s:
            ...
            s.set_attribute("diagnosis.confidence", conf)  # if s is not None
    """
    if not _enabled or _tracer is None:
        yield None
        return
    with _tracer.start_as_current_span(name) as current:
        for key, value in attributes.items():
            if value is not None:
                current.set_attribute(key, value)
        yield current
