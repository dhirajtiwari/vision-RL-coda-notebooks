"""Contextual / multi-armed bandits for next-best diagnostic action.

Best first RL layer for this product: partial feedback, safer than full MDP,
online-updatable from claim outcomes.

Algorithms:
  - EpsilonGreedy
  - UCB1 (Auer et al.)
  - LinUCB (Li et al. 2010) — contextual
  - ThompsonSampling (Beta-Bernoulli) — non-contextual baseline
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class BanditStats:
    pulls: np.ndarray
    rewards: np.ndarray

    @classmethod
    def zeros(cls, n_arms: int) -> BanditStats:
        return cls(pulls=np.zeros(n_arms), rewards=np.zeros(n_arms))


class EpsilonGreedy:
    def __init__(self, n_arms: int, epsilon: float = 0.1, seed: int = 42):
        self.n_arms = n_arms
        self.epsilon = epsilon
        self.stats = BanditStats.zeros(n_arms)
        self.rng = np.random.default_rng(seed)

    def select(self, context: np.ndarray | None = None) -> int:
        if self.rng.random() < self.epsilon:
            return int(self.rng.integers(0, self.n_arms))
        means = self.stats.rewards / np.maximum(self.stats.pulls, 1)
        return int(np.argmax(means))

    def update(self, arm: int, reward: float, context: np.ndarray | None = None) -> None:
        self.stats.pulls[arm] += 1
        self.stats.rewards[arm] += reward


class UCB1:
    """Auer, Cesa-Bianchi, Fischer — Finite-time Analysis of the Multiarmed Bandit Problem."""

    def __init__(self, n_arms: int, c: float = 2.0):
        self.n_arms = n_arms
        self.c = c
        self.stats = BanditStats.zeros(n_arms)
        self.t = 0

    def select(self, context: np.ndarray | None = None) -> int:
        self.t += 1
        for a in range(self.n_arms):
            if self.stats.pulls[a] == 0:
                return a
        means = self.stats.rewards / self.stats.pulls
        bonus = self.c * np.sqrt(np.log(self.t) / self.stats.pulls)
        return int(np.argmax(means + bonus))

    def update(self, arm: int, reward: float, context: np.ndarray | None = None) -> None:
        self.stats.pulls[arm] += 1
        self.stats.rewards[arm] += reward


class ThompsonSampling:
    """Beta-Bernoulli Thompson sampling (rewards mapped to [0,1] success proxy)."""

    def __init__(self, n_arms: int, seed: int = 42):
        self.n_arms = n_arms
        self.alpha = np.ones(n_arms)
        self.beta = np.ones(n_arms)
        self.rng = np.random.default_rng(seed)

    def select(self, context: np.ndarray | None = None) -> int:
        samples = self.rng.beta(self.alpha, self.beta)
        return int(np.argmax(samples))

    def update(self, arm: int, reward: float, context: np.ndarray | None = None) -> None:
        # map reward roughly to success Bernoulli
        p = 1.0 / (1.0 + np.exp(-reward / 5.0))
        if self.rng.random() < p:
            self.alpha[arm] += 1
        else:
            self.beta[arm] += 1


class LinUCB:
    """LinUCB (Li, Chu, Langford, Schapire — WWW 2010).

    Maintains ridge-regression confidence bounds per arm.
    """

    def __init__(self, n_arms: int, d: int, alpha: float = 0.5, lam: float = 1.0):
        self.n_arms = n_arms
        self.d = d
        self.alpha = alpha
        self.A = [lam * np.eye(d) for _ in range(n_arms)]
        self.b = [np.zeros((d, 1)) for _ in range(n_arms)]

    def select(self, context: np.ndarray) -> int:
        x = np.asarray(context, dtype=np.float64).reshape(-1, 1)
        scores = []
        for a in range(self.n_arms):
            A_inv = np.linalg.inv(self.A[a])
            theta = A_inv @ self.b[a]  # (d, 1)
            mean = float((theta.T @ x).item())
            bonus = float(np.sqrt((x.T @ A_inv @ x).item()))
            scores.append(mean + self.alpha * bonus)
        return int(np.argmax(scores))

    def update(self, arm: int, reward: float, context: np.ndarray) -> None:
        x = np.asarray(context, dtype=np.float64).reshape(-1, 1)
        self.A[arm] += x @ x.T
        self.b[arm] += float(reward) * x


def run_bandit_on_mdp(
    env,
    policy,
    n_episodes: int = 500,
    contextual: bool = False,
) -> dict:
    """One-shot bandit: pick a single first diagnostic action; reward = episode return."""
    cumulative = []
    total = 0.0
    for ep in range(n_episodes):
        env.reset()
        # first-action bandit: only use context features (no step bits) for LinUCB d
        if contextual:
            x = np.asarray(env.context.feature_vector(), dtype=np.float64)
            arm = policy.select(x)
        else:
            arm = policy.select(None)
        # play only this arm then greedy random until done for remainder — bandit reward
        # = immediate step quality proxy: run full episode with this first action then random
        tr = env.step(arm)
        ep_r = tr.reward
        while not tr.done:
            # random remaining (bandit only optimizes first action in this demo)
            a = int(np.random.randint(0, env.n_actions))
            tr = env.step(a)
            ep_r += tr.reward
        if contextual:
            policy.update(arm, ep_r, x)
        else:
            policy.update(arm, ep_r)
        total += ep_r
        cumulative.append(total / (ep + 1))
    return {"mean_return": cumulative[-1], "curve": cumulative}
