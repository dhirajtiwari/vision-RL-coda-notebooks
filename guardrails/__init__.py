"""
Guardrails package (kickoff prompt §E, handbook ch05).

Enforcement lives OUTSIDE the model, in code — never merely requested in a
prompt. For this deterministic graph-native app the primary risks are:

- injection into free-text ``message`` (Cypher injection is already mitigated by
  parameterised Neo4j queries; we add an explicit input sanitiser + assertions),
- PII leakage in responses/telemetry (redaction),
- oversized / malformed outputs,
- abusive request volume (rate limiting).

Guardrails fail CLOSED for security controls: on a guardrail error we reject the
request rather than pass it through.
"""

from guardrails.input import GuardrailViolation, check_input
from guardrails.output import cap_length, validate_output
from guardrails.pipeline import guard_request
from guardrails.rate_limit import RateLimiter

__all__ = [
    "check_input",
    "GuardrailViolation",
    "validate_output",
    "cap_length",
    "guard_request",
    "RateLimiter",
]
