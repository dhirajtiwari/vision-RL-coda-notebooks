"""Reward design for diagnostic decision policies.

Enterprise rule: rewards must be auditable and preferably offline-evaluable
from claim outcomes — not pure clickbait engagement.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RewardConfig:
    # Resolve correct FM / customer fixed issue
    resolve_success: float = 10.0
    # Wrong path / wrong parts ordered
    resolve_failure: float = -8.0
    # Per diagnostic step effort (negative)
    step_cost_scale: float = -1.0
    # Escalation: sometimes correct, always costly
    escalate_base: float = -3.0
    escalate_if_needed: float = 4.0  # net positive if truly needs tech
    # Safety: never reward inventing codes / skipping required safety steps
    safety_violation: float = -20.0


DEFAULT_REWARD = RewardConfig()


def step_reward(step_cost: float, cfg: RewardConfig = DEFAULT_REWARD) -> float:
    return cfg.step_cost_scale * step_cost


def terminal_reward(
    *,
    success: bool,
    escalated: bool,
    escalation_was_needed: bool,
    cfg: RewardConfig = DEFAULT_REWARD,
) -> float:
    r = 0.0
    if success:
        r += cfg.resolve_success
    else:
        r += cfg.resolve_failure
    if escalated:
        r += cfg.escalate_base
        if escalation_was_needed:
            r += cfg.escalate_if_needed
    return r
