"""
Input guardrails (kickoff prompt §E).

Detects and blocks:
- prompt-injection / jailbreak style phrases in free text,
- Cypher/SQL injection tokens (defence-in-depth on top of parameterised queries),
- control characters and excessively long input.

Returns a normalised, sanitised string or raises :class:`GuardrailViolation`
(fail-closed for security-relevant hits).
"""

from __future__ import annotations

import re


class GuardrailViolation(Exception):
    """Raised when input fails a security guardrail (fail-closed)."""

    def __init__(self, rule: str, detail: str = "") -> None:
        self.rule = rule
        self.detail = detail
        super().__init__(f"guardrail:{rule} {detail}".strip())


# Injection / jailbreak heuristics (regex layer; a classifier can be added later).
_INJECTION_PATTERNS = [
    re.compile(r"ignore (all|any|previous|prior) (instruction|prompt)", re.IGNORECASE),
    re.compile(r"disregard (the|all|previous)", re.IGNORECASE),
    re.compile(r"you are now|act as (an?|the) (admin|root|system)", re.IGNORECASE),
    re.compile(r"reveal (your|the) (system )?prompt", re.IGNORECASE),
]

# Cypher/SQL injection tokens — defence in depth (queries are parameterised).
_CYPHER_INJECTION = re.compile(
    r"(?i)(;\s*(match|create|merge|delete|detach|drop|set)\b|\bcall\s+db\.|" r"\bunion\b|--\s|/\*|\*/)"
)

_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def check_input(text: str, *, max_length: int = 2000) -> str:
    """Validate and sanitise free-text user input.

    Returns the cleaned string. Raises :class:`GuardrailViolation` on a
    security hit (injection/jailbreak/cypher tokens).
    """
    if text is None:
        raise GuardrailViolation("empty_input", "message is required")
    cleaned = _CONTROL_CHARS.sub("", text).strip()
    if not cleaned:
        raise GuardrailViolation("empty_input", "message is empty after sanitisation")
    if len(cleaned) > max_length:
        # Hard cap rather than silent truncation so callers see the boundary.
        raise GuardrailViolation("too_long", f"len={len(cleaned)} max={max_length}")

    for pattern in _INJECTION_PATTERNS:
        if pattern.search(cleaned):
            raise GuardrailViolation("prompt_injection", pattern.pattern)

    if _CYPHER_INJECTION.search(cleaned):
        raise GuardrailViolation("cypher_injection", "suspicious graph query tokens")

    return cleaned
