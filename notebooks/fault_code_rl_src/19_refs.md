## Part 10 — Commands, references, client talking points

### Commands

```bash
pip install -r requirements-ml.txt

# Bandit bake-off
python -m ml.fault_code_rl.train --algo bandit --episodes 800 \
  --out notebooks/fault_code_rl_artifacts/bandit

# Tabular Q
python -m ml.fault_code_rl.train --algo q --episodes 1500 \
  --out notebooks/fault_code_rl_artifacts/q_policy.pt

# DQN on client CUDA
python -m ml.fault_code_rl.train --algo dqn --episodes 800 --require-cuda \
  --out models/artifacts/rl/dqn.pt

python -m ml.fault_code_rl.eval_rl \
  --q-table notebooks/fault_code_rl_artifacts/q_policy.npz \
  --dqn models/artifacts/rl/dqn.pt \
  --min-success-rate 0.35
```

### References

1. Sutton & Barto — *Reinforcement Learning: An Introduction* (MDP, Q-learning)
2. Auer et al. — UCB1 finite-time bandit analysis
3. Li et al. — *A Contextual-Bandit Approach to Personalized News Article Recommendation* (LinUCB, WWW 2010)
4. Mnih et al. — *Human-level control through deep RL* (DQN, Nature 2015)
5. Levine et al. — Offline RL tutorials / batch RL surveys
6. This repo LLMOps: `docs/sdd/09-PLATFORM-LLMOPS.md`

### Client talking points (30 seconds)

1. **Core diagnosis stays GraphRAG** — auditable, versioned knowledge.
2. **RL is optional optimization** of *which eligible step next*, using claim outcomes as reward.
3. We start with **contextual bandits + offline eval**, not wild online exploration.
4. **DQN + CUDA** is available for multi-step policies when data justifies it — **same GPU image** as vision training.
5. Safety: **action masks**, shadow mode, registry pins, canary rollback.

---

### Artifacts from this notebook

```text
notebooks/fault_code_rl_artifacts/
  bandit_curves.png
  q_learning_curve.png
  dqn_curves.png
  q_policy.npz
  dqn_policy.pt
  rl_eval_report.json
  rl_mlops_checklist.csv
  executive_summary.json
```

**Done when:** client sees theory + math + working bandit/Q/DQN, CUDA path documented, and a clear “when RL / when not” story integrated with GraphRAG.
