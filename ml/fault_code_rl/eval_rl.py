"""Evaluate learned policies vs baselines on DiagnosticMDP."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch

from ml.fault_code_rl.device import pick_device
from ml.fault_code_rl.domain import STEP_IDS
from ml.fault_code_rl.dqn import QNet, dqn_act
from ml.fault_code_rl.mdp import DiagnosticMDP


def evaluate_random(env: DiagnosticMDP, n: int = 200, seed: int = 0) -> dict:
    rng = np.random.default_rng(seed)
    returns, succ = [], []
    for _ in range(n):
        env.reset()
        done, ep_r, ok = False, 0.0, False
        while not done:
            tr = env.step(int(rng.integers(0, env.n_actions)))
            ep_r += tr.reward
            done = tr.done
            ok = ok or bool(tr.info.get("success"))
        returns.append(ep_r)
        succ.append(float(ok))
    return {"mean_return": float(np.mean(returns)), "success_rate": float(np.mean(succ)), "n": n}


def evaluate_q_table(Q: np.ndarray, env: DiagnosticMDP, n: int = 200) -> dict:
    returns, succ = [], []
    for _ in range(n):
        s = env.reset()
        done, ep_r, ok = False, 0.0, False
        while not done:
            a = int(np.argmax(Q[s]))
            tr = env.step(a)
            s = tr.next_state
            ep_r += tr.reward
            done = tr.done
            ok = ok or bool(tr.info.get("success"))
        returns.append(ep_r)
        succ.append(float(ok))
    return {"mean_return": float(np.mean(returns)), "success_rate": float(np.mean(succ)), "n": n}


def evaluate_dqn_ckpt(path: Path, env: DiagnosticMDP, n: int = 200) -> dict:
    device = pick_device()
    ckpt = torch.load(path, map_location=device, weights_only=False)
    net = QNet(ckpt["obs_dim"], ckpt["n_actions"]).to(device)
    net.load_state_dict(ckpt["policy"])
    net.eval()
    returns, succ = [], []
    for _ in range(n):
        env.reset()
        s = env.encode_state_features()
        done, ep_r, ok = False, 0.0, False
        while not done:
            a = dqn_act(net, s, device)
            tr = env.step(a)
            s = env.encode_state_features()
            ep_r += tr.reward
            done = tr.done
            ok = ok or bool(tr.info.get("success"))
        returns.append(ep_r)
        succ.append(float(ok))
    return {"mean_return": float(np.mean(returns)), "success_rate": float(np.mean(succ)), "n": n}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--q-table", type=Path, default=None)
    p.add_argument("--dqn", type=Path, default=None)
    p.add_argument("--episodes", type=int, default=200)
    p.add_argument("--min-success-rate", type=float, default=0.0)
    p.add_argument("--report", type=Path, default=None)
    args = p.parse_args(argv)

    env = DiagnosticMDP(seed=123)
    report = {"random": evaluate_random(env, n=args.episodes, seed=1), "steps": STEP_IDS}
    if args.q_table:
        data = np.load(args.q_table)
        report["q_learning"] = evaluate_q_table(data["Q"], DiagnosticMDP(seed=123), n=args.episodes)
    if args.dqn:
        report["dqn"] = evaluate_dqn_ckpt(args.dqn, DiagnosticMDP(seed=123), n=args.episodes)

    print(json.dumps(report, indent=2))
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2))

    # gate on best learned policy if present
    best = 0.0
    for k in ("q_learning", "dqn"):
        if k in report:
            best = max(best, report[k]["success_rate"])
    if best < args.min_success_rate:
        print(f"FAIL success_rate {best:.3f} < {args.min_success_rate}")
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
