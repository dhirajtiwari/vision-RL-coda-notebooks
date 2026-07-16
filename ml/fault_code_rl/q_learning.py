"""Tabular Q-learning on DiagnosticMDP (Sutton & Barto).

Q(s,a) ← Q(s,a) + α [ r + γ max_a' Q(s',a') − Q(s,a) ]
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ml.fault_code_rl.mdp import DiagnosticMDP


@dataclass
class QLearningConfig:
    alpha: float = 0.15
    gamma: float = 0.95
    epsilon_start: float = 1.0
    epsilon_end: float = 0.05
    epsilon_decay_episodes: int = 800
    episodes: int = 1500
    seed: int = 42


class TabularQAgent:
    def __init__(self, n_states: int, n_actions: int, cfg: QLearningConfig = QLearningConfig()):
        self.n_actions = n_actions
        self.cfg = cfg
        self.Q = np.zeros((n_states, n_actions), dtype=np.float64)
        self.rng = np.random.default_rng(cfg.seed)

    def epsilon(self, episode: int) -> float:
        t = min(1.0, episode / max(self.cfg.epsilon_decay_episodes, 1))
        return self.cfg.epsilon_start + t * (self.cfg.epsilon_end - self.cfg.epsilon_start)

    def act(self, state: int, episode: int) -> int:
        if self.rng.random() < self.epsilon(episode):
            return int(self.rng.integers(0, self.n_actions))
        return int(np.argmax(self.Q[state]))

    def update(self, s: int, a: int, r: float, s2: int, done: bool) -> None:
        target = r if done else r + self.cfg.gamma * np.max(self.Q[s2])
        self.Q[s, a] += self.cfg.alpha * (target - self.Q[s, a])


def train_q_learning(env: DiagnosticMDP | None = None, cfg: QLearningConfig | None = None) -> dict:
    cfg = cfg or QLearningConfig()
    env = env or DiagnosticMDP(seed=cfg.seed)
    agent = TabularQAgent(env.n_states, env.n_actions, cfg)
    returns = []
    successes = []
    for ep in range(cfg.episodes):
        s = env.reset()
        done = False
        ep_r = 0.0
        success = False
        while not done:
            a = agent.act(s, ep)
            tr = env.step(a)
            agent.update(s, a, tr.reward, tr.next_state, tr.done)
            s = tr.next_state
            ep_r += tr.reward
            done = tr.done
            if tr.info.get("success"):
                success = True
        returns.append(ep_r)
        successes.append(float(success))
    window = 100
    moving = [float(np.mean(returns[max(0, i - window) : i + 1])) for i in range(len(returns))]
    return {
        "agent": agent,
        "returns": returns,
        "moving_avg_return": moving,
        "success_rate_last_100": float(np.mean(successes[-100:])),
        "mean_return_last_100": float(np.mean(returns[-100:])),
        "Q": agent.Q,
        "cfg": cfg,
    }


def greedy_policy_steps(agent: TabularQAgent, state: int = 0, max_steps: int = 4) -> list[int]:
    """Roll out greedy policy from empty bitmask state (ignores stochastic env)."""
    s = state
    actions = []
    for _ in range(max_steps):
        a = int(np.argmax(agent.Q[s]))
        actions.append(a)
        s = s | (1 << a)
    return actions
