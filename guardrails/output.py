"""
Output guardrails (kickoff prompt §E).

For the deterministic path the model does not generate free text, but responses
still flow to a browser, so we:
- cap response length,
- optionally redact PII from the natural-language ``response`` field,
- ensure the payload is JSON-serialisable and schema-shaped (Pydantic already
  enforces the top-level schema at the API boundary).
"""

from __future__ import annotations

from typing import Any


def cap_length(text: str, *, max_chars: int = 8000) -> str:
    """Cap a natural-language response, appending a truncation marker."""
    if text is None:
        return ""
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 20].rstrip() + "\n…[truncated]"


def validate_output(
    payload: dict[str, Any],
    *,
    max_chars: int = 8000,
    redact_pii: bool = True,
) -> dict[str, Any]:
    """Apply output guardrails to a diagnosis response dict in place.

    - caps the ``response`` string,
    - redacts PII in the ``response`` string when enabled.
    """
    response = payload.get("response")
    if isinstance(response, str):
        response = cap_length(response, max_chars=max_chars)
        if redact_pii:
            from observability.redaction import redact

            response = redact(response)
        payload["response"] = response
    return payload
