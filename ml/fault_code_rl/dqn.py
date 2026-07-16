"""Deep Q-Network for DiagnosticMDP (Mnih et al. 2015 style, small net).

Uses CUDA/MPS/CPU via ml.fault_code_rl.device — same client hardware story as vision.
"""

from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from ml.fault_code_rl.device import assert_cuda_for_client_train, device_report
from ml.fault_code_rl.mdp import DiagnosticMDP


class QNet(nn.Module):
    def __init__(self, obs_dim: int, n_actions: int, hidden: int = 128):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(obs_dim, hidden),
            nn.ReLU(),
            nn.Linear(hidden, hidden),
            nn.ReLU(),
            nn.Linear(hidden, n_actions),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


@dataclass
class DQNConfig:
    episodes: int = 600
    gamma: float = 0.95
    lr: float = 1e-3
    batch_size: int = 64
    buffer_size: int = 10_000
    warmup: int = 500
    target_sync: int = 100
    epsilon_start: float = 1.0
    epsilon_end: float = 0.05
    epsilon_decay: int = 400
    seed: int = 42
    require_cuda: bool = False


class ReplayBuffer:
    def __init__(self, capacity: int):
        self.buf: deque = deque(maxlen=capacity)

    def push(self, *transition) -> None:
        self.buf.append(transition)

    def sample(self, batch_size: int):
        batch = random.sample(self.buf, batch_size)
        return map(np.array, zip(*batch, strict=False))

    def __len__(self) -> int:
        return len(self.buf)


def train_dqn(cfg: DQNConfig | None = None, env: DiagnosticMDP | None = None) -> dict:
    cfg = cfg or DQNConfig()
    random.seed(cfg.seed)
    np.random.seed(cfg.seed)
    torch.manual_seed(cfg.seed)

    device = assert_cuda_for_client_train(allow_cpu_fallback=not cfg.require_cuda)
    env = env or DiagnosticMDP(seed=cfg.seed)
    # probe obs dim
    env.reset()
    obs_dim = env.encode_state_features().shape[0]
    n_actions = env.n_actions

    policy = QNet(obs_dim, n_actions).to(device)
    target = QNet(obs_dim, n_actions).to(device)
    target.load_state_dict(policy.state_dict())
    opt = torch.optim.Adam(policy.parameters(), lr=cfg.lr)
    buffer = ReplayBuffer(cfg.buffer_size)

    returns = []
    losses = []
    global_step = 0

    def epsilon(ep: int) -> float:
        t = min(1.0, ep / max(cfg.epsilon_decay, 1))
        return cfg.epsilon_start + t * (cfg.epsilon_end - cfg.epsilon_start)

    for ep in range(cfg.episodes):
        env.reset()
        s = env.encode_state_features()
        done = False
        ep_r = 0.0
        while not done:
            if random.random() < epsilon(ep):
                a = random.randrange(n_actions)
            else:
                with torch.no_grad():
                    q = policy(torch.tensor(s, device=device).unsqueeze(0))
                    a = int(q.argmax(dim=1).item())
            tr = env.step(a)
            s2 = env.encode_state_features()
            buffer.push(s, a, tr.reward, s2, float(tr.done))
            s = s2
            ep_r += tr.reward
            done = tr.done
            global_step += 1

            if len(buffer) >= cfg.warmup:
                states, actions, rewards, next_states, dones = buffer.sample(cfg.batch_size)
                states_t = torch.tensor(states, dtype=torch.float32, device=device)
                actions_t = torch.tensor(actions, dtype=torch.int64, device=device)
                rewards_t = torch.tensor(rewards, dtype=torch.float32, device=device)
                next_states_t = torch.tensor(next_states, dtype=torch.float32, device=device)
                dones_t = torch.tensor(dones, dtype=torch.float32, device=device)

                q_sa = policy(states_t).gather(1, actions_t.unsqueeze(1)).squeeze(1)
                with torch.no_grad():
                    max_next = target(next_states_t).max(dim=1).values
                    y = rewards_t + cfg.gamma * max_next * (1.0 - dones_t)
                loss = F.mse_loss(q_sa, y)
                opt.zero_grad(set_to_none=True)
                loss.backward()
                opt.step()
                losses.append(float(loss.item()))

            if global_step % cfg.target_sync == 0:
                target.load_state_dict(policy.state_dict())

        returns.append(ep_r)

    return {
        "policy": policy,
        "target": target,
        "device": str(device),
        "device_report": device_report(),
        "returns": returns,
        "losses": losses,
        "mean_return_last_100": float(np.mean(returns[-100:])),
        "obs_dim": obs_dim,
        "n_actions": n_actions,
        "cfg": cfg,
    }


@torch.no_grad()
def dqn_act(policy: QNet, obs: np.ndarray, device: torch.device) -> int:
    q = policy(torch.tensor(obs, dtype=torch.float32, device=device).unsqueeze(0))
    return int(q.argmax(dim=1).item())
