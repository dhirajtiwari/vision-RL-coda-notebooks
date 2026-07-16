"""Offline / batch RL considerations for enterprise diagnostics.

Live ε-greedy exploration on real customers is often unacceptable.
Prefer:
  - log historical (context, action=step suggested, reward=claim outcome)
  - offline policy evaluation (IPS / DR)
  - constrained policies that only re-rank graph-eligible steps
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class LoggedDecision:
    context: np.ndarray
    action: int
    reward: float
    propensity: float  # π_b(a|x) of behavior policy that generated log


def inverse_propensity_score(
    dataset: list[LoggedDecision],
    target_actions: list[int],
) -> float:
    """Simple IPS estimate of policy that always takes target_actions[i] for sample i.

    V_IPS = (1/N) Σ 1[a_i = π(x_i)] * r_i / π_b(a_i|x_i)
    """
    vals = []
    for row, a_target in zip(dataset, target_actions, strict=False):
        if row.action == a_target:
            vals.append(row.reward / max(row.propensity, 1e-6))
        else:
            vals.append(0.0)
    return float(np.mean(vals)) if vals else 0.0


def behavior_log_from_random_policy(
    env,
    n: int = 1000,
    seed: int = 0,
) -> list[LoggedDecision]:
    """Simulate logged bandit data under uniform behavior policy."""
    rng = np.random.default_rng(seed)
    logs: list[LoggedDecision] = []
    p = 1.0 / env.n_actions
    for _ in range(n):
        env.reset()
        x = np.asarray(env.context.feature_vector(), dtype=np.float64)
        a = int(rng.integers(0, env.n_actions))
        # one-step reward proxy: take action then finish with random until done
        tr = env.step(a)
        r = tr.reward
        while not tr.done:
            tr = env.step(int(rng.integers(0, env.n_actions)))
            r += tr.reward
        logs.append(LoggedDecision(context=x, action=a, reward=r, propensity=p))
    return logs


def safety_mask_graph_eligible(
    n_actions: int,
    eligible: list[int],
) -> np.ndarray:
    """Binary mask: only GraphRAG-eligible diagnostic steps may be chosen."""
    m = np.zeros(n_actions, dtype=np.float32)
    for a in eligible:
        if 0 <= a < n_actions:
            m[a] = 1.0
    if m.sum() == 0:
        m[:] = 1.0  # fail-open to full set only if empty — production should fail-closed
    return m


def masked_argmax(q_values: np.ndarray, mask: np.ndarray) -> int:
    masked = np.where(mask > 0, q_values, -1e9)
    return int(np.argmax(masked))
