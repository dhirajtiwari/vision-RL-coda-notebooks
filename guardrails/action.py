"""
Action guardrails (kickoff prompt §E — agentic controls, handbook ch05/ch10).

The current diagnosis flow is deterministic and does not let a model invoke
tools, but escalation/claim actions ARE side-effecting. This module provides a
default-deny allowlist + argument validation + human-in-the-loop flag that any
future agentic tool-calling MUST route through, and that the escalation/claims
integrations can adopt for least-privilege enforcement.
"""

from __future__ import annotations

from dataclasses import dataclass, field


class ActionDenied(Exception):
    """Raised when an action is not on the allowlist or fails validation."""


@dataclass(frozen=True)
class ActionPolicy:
    """Least-privilege policy for a single named action."""

    name: str
    allowed: bool = False
    requires_human_approval: bool = False
    required_args: frozenset[str] = field(default_factory=frozenset)


# Default-deny registry. Add entries explicitly; anything not listed is denied.
_POLICIES: dict[str, ActionPolicy] = {
    "submit_claim": ActionPolicy(
        name="submit_claim",
        allowed=True,
        requires_human_approval=True,  # high-impact / financial
        required_args=frozenset({"diagnosis_id", "customer_id"}),
    ),
    "escalate_case": ActionPolicy(
        name="escalate_case",
        allowed=True,
        requires_human_approval=False,
        required_args=frozenset({"session_id", "reason"}),
    ),
    "update_claim_status": ActionPolicy(
        name="update_claim_status",
        allowed=True,
        requires_human_approval=True,
        required_args=frozenset({"claim_id", "status"}),
    ),
}


def authorize_action(name: str, args: dict, *, human_approved: bool = False) -> None:
    """Authorize a side-effecting action. Raises :class:`ActionDenied` if denied.

    Fail-closed: unknown actions and missing args are rejected.
    """
    policy = _POLICIES.get(name)
    if policy is None or not policy.allowed:
        raise ActionDenied(f"action '{name}' is not on the allowlist (default-deny)")
    missing = policy.required_args - set(args or {})
    if missing:
        raise ActionDenied(f"action '{name}' missing required args: {sorted(missing)}")
    if policy.requires_human_approval and not human_approved:
        raise ActionDenied(f"action '{name}' requires human approval (HITL)")
