"""
PII redaction (kickoff prompt §E/§H, GDPR).

Deterministic, dependency-free regex redaction applied to:
- log lines (via JSON formatter),
- telemetry attributes,
- optionally API responses.

This is intentionally conservative: it redacts obvious direct identifiers
(emails, phones, serials, customer/asset ids, credit-card-like and government
id-like numbers). It is NOT a substitute for a data-classification review — see
docs/governance/data-classification.md.
"""

from __future__ import annotations

import re

# Order matters: more specific patterns first.
_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("[EMAIL]", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")),
    # E.164-ish / common phone formats
    ("[PHONE]", re.compile(r"\b\+?\d{1,3}[\s.-]?\(?\d{2,4}\)?[\s.-]?\d{3,4}[\s.-]?\d{3,4}\b")),
    # 13-19 digit card-like numbers (with optional separators)
    ("[CARD]", re.compile(r"\b(?:\d[ -]?){13,19}\b")),
    # customer/asset/serial identifiers used across this project
    ("[CUSTOMER_ID]", re.compile(r"\bCUST-[A-Z0-9]{4,}\b", re.IGNORECASE)),
    ("[ASSET_ID]", re.compile(r"\bASSET-[A-Z0-9]{4,}\b", re.IGNORECASE)),
    ("[SERIAL]", re.compile(r"\b(?:SN|SER|SERIAL)[-:]?[A-Z0-9]{6,}\b", re.IGNORECASE)),
]

# Keys whose *values* should always be masked when redacting structured dicts.
_SENSITIVE_KEYS = {
    "customer_id",
    "asset_id",
    "serial",
    "serial_number",
    "email",
    "phone",
    "password",
    "token",
    "api_key",
    "authorization",
}


def redact(text: str) -> str:
    """Redact direct identifiers from a free-text string."""
    if not text:
        return text
    for replacement, pattern in _PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def redact_mapping(data: dict, *, _depth: int = 0) -> dict:
    """Recursively redact a dict for safe logging/telemetry (max depth 6)."""
    if _depth > 6:
        return {"_truncated": True}
    out: dict = {}
    for key, value in data.items():
        lkey = str(key).lower()
        if lkey in _SENSITIVE_KEYS:
            out[key] = "[REDACTED]"
        elif isinstance(value, dict):
            out[key] = redact_mapping(value, _depth=_depth + 1)
        elif isinstance(value, str):
            out[key] = redact(value)
        elif isinstance(value, list):
            out[key] = [
                redact_mapping(v, _depth=_depth + 1)
                if isinstance(v, dict)
                else (redact(v) if isinstance(v, str) else v)
                for v in value
            ]
        else:
            out[key] = value
    return out
