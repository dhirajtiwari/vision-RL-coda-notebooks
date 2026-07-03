"""
Guardrail pipeline (kickoff prompt §E, handbook ch05).

Composes input + output guardrails into a single provider-agnostic entry point
used by the API layer. Security controls fail CLOSED.
"""

from __future__ import annotations

from typing import Any

from guardrails.input import GuardrailViolation, check_input
from guardrails.output import validate_output


def guard_input(message: str, *, max_length: int = 2000) -> str:
    """Run input guardrails; returns sanitised text or raises GuardrailViolation."""
    return check_input(message, max_length=max_length)


def guard_output(
    payload: dict[str, Any],
    *,
    max_chars: int = 8000,
    redact_pii: bool = True,
) -> dict[str, Any]:
    """Run output guardrails on a response dict."""
    return validate_output(payload, max_chars=max_chars, redact_pii=redact_pii)


def guard_request(
    message: str,
    *,
    max_input_length: int = 2000,
) -> str:
    """Convenience wrapper for the request-entry guardrail.

    Kept separate from output so the API can sanitise input, run the
    (deterministic) diagnosis, then guard the output.
    """
    return guard_input(message, max_length=max_input_length)


__all__ = ["guard_input", "guard_output", "guard_request", "GuardrailViolation"]
