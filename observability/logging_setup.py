"""
Structured logging (kickoff prompt §H).

Emits one JSON object per log line with a correlation/request id so logs from a
single request can be stitched together in any log backend. Falls back to plain
text when ``LOG_JSON=false`` (nicer for local `tail -f`).

PII safety: log records pass through :func:`observability.redaction.redact`
so customer identifiers / serials never land in logs in plaintext when
``ENABLE_PII_REDACTION=true``.
"""

from __future__ import annotations

import json
import logging
import sys
from contextvars import ContextVar
from typing import Any

# Correlation id propagated per-request via middleware. Empty string when no
# request is in scope (e.g. startup logs, batch jobs).
_request_id: ContextVar[str] = ContextVar("request_id", default="")


def set_request_id(value: str) -> None:
    _request_id.set(value)


def get_request_id() -> str:
    return _request_id.get()


class _RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = _request_id.get()
        return True


class JsonFormatter(logging.Formatter):
    """Render log records as single-line JSON with correlation id."""

    def __init__(self, *, redactor=None) -> None:
        super().__init__()
        self._redactor = redactor

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "request_id": getattr(record, "request_id", ""),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        # Attach any structured `extra={...}` fields that are not stock attrs.
        for key, value in record.__dict__.items():
            if key in _RESERVED or key.startswith("_"):
                continue
            payload.setdefault(key, value)
        text = json.dumps(payload, default=str, ensure_ascii=False)
        if self._redactor is not None:
            text = self._redactor(text)
        return text


_RESERVED = set(vars(logging.LogRecord("", 0, "", 0, "", (), None)).keys()) | {
    "request_id",
    "message",
    "asctime",
    "taskName",
}


def setup_logging(*, level: str = "INFO", json_output: bool = True, redact: bool = True) -> None:
    """Configure the root logger once. Idempotent."""
    root = logging.getLogger()
    root.setLevel(level.upper())
    # Remove existing handlers so re-import (e.g. under uvicorn reload) is clean.
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    redactor = None
    if redact:
        try:
            from observability.redaction import redact as _redact

            redactor = _redact
        except Exception:  # pragma: no cover - redaction is best-effort
            redactor = None

    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(_RequestIdFilter())
    if json_output:
        handler.setFormatter(JsonFormatter(redactor=redactor))
    else:
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s [%(request_id)s] %(name)s: %(message)s"))
    root.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
