"""CLI train entrypoints for RL showcase policies.

python -m ml.fault_code_rl.train --algo q --episodes 1000
python -m ml.fault_code_rl.train --algo dqn --episodes 400 --require-cuda
python -m ml.fault_code_rl.train --algo bandit --episodes 800
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch

from ml.fault_code_rl.bandits import UCB1, EpsilonGreedy, LinUCB, run_bandit_on_mdp
from ml.fault_code_rl.device import device_report
from ml.fault_code_rl.domain import STEP_IDS
from ml.fault_code_rl.dqn import DQNConfig, train_dqn
from ml.fault_code_rl.mdp import DiagnosticMDP
from ml.fault_code_rl.q_learning import QLearningConfig, train_q_learning


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Train diagnostic RL policies")
    p.add_argument("--algo", choices=["q", "dqn", "bandit"], default="q")
    p.add_argument("--episodes", type=int, default=800)
    p.add_argument("--out", type=Path, default=Path("notebooks/fault_code_rl_artifacts/policy.pt"))
    p.add_argument("--require-cuda", action="store_true")
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args(argv)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    print("device_report:", json.dumps(device_report(), indent=2))

    if args.algo == "q":
        result = train_q_learning(cfg=QLearningConfig(episodes=args.episodes, seed=args.seed))
        np.savez(
            args.out.with_suffix(".npz"),
            Q=result["Q"],
            mean_return_last_100=result["mean_return_last_100"],
            success_rate_last_100=result["success_rate_last_100"],
        )
        metrics = {
            "algo": "q_learning",
            "mean_return_last_100": result["mean_return_last_100"],
            "success_rate_last_100": result["success_rate_last_100"],
            "steps": STEP_IDS,
        }
        print(json.dumps(metrics, indent=2))
        args.out.with_suffix(".metrics.json").write_text(json.dumps(metrics, indent=2))
        return 0

    if args.algo == "dqn":
        result = train_dqn(
            DQNConfig(
                episodes=args.episodes,
                seed=args.seed,
                require_cuda=args.require_cuda,
            )
        )
        torch.save(
            {
                "policy": result["policy"].state_dict(),
                "obs_dim": result["obs_dim"],
                "n_actions": result["n_actions"],
                "steps": STEP_IDS,
                "device_report": result["device_report"],
            },
            args.out,
        )
        metrics = {
            "algo": "dqn",
            "device": result["device"],
            "mean_return_last_100": result["mean_return_last_100"],
        }
        print(json.dumps(metrics, indent=2))
        args.out.with_suffix(".metrics.json").write_text(json.dumps(metrics, indent=2))
        return 0

    # bandit comparison
    env = DiagnosticMDP(seed=args.seed)
    d = len(env.context.feature_vector())
    results = {}
    for name, policy, contextual in [
        ("epsilon_greedy", EpsilonGreedy(env.n_actions, epsilon=0.1, seed=args.seed), False),
        ("ucb1", UCB1(env.n_actions), False),
        ("linucb", LinUCB(env.n_actions, d=d, alpha=0.6), True),
    ]:
        env = DiagnosticMDP(seed=args.seed)
        out = run_bandit_on_mdp(env, policy, n_episodes=args.episodes, contextual=contextual)
        results[name] = {"mean_return": out["mean_return"]}
        print(name, out["mean_return"])
    args.out.with_suffix(".bandit.json").write_text(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
