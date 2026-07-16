# Diagnostic reinforcement learning

Optional RL layer for **next-best diagnostic step / multi-step session policy** on top of GraphRAG — not a replacement for Neo4j reasoning.

| Artifact | Purpose |
|----------|---------|
| [`fault_code_rl_playbook.ipynb`](./fault_code_rl_playbook.ipynb) | Theory, math, bandits, Q-learning, DQN+CUDA, offline IPS, checklist |
| [`../ml/fault_code_rl/`](../ml/fault_code_rl/) | Simulator, algorithms, train/eval CLIs |
| [`../evals/rl/`](../evals/rl/) | Eval docs + floors in `thresholds.yaml` |
| [`../docker/Dockerfile.ml`](../docker/Dockerfile.ml) | Shared CUDA image with vision |
| Registry aliases | `diagnosis-step-bandit`, `diagnosis-session-dqn` (inactive) |

## Which RL?

| Use case | Algorithm |
|----------|-----------|
| Next step ranking | Contextual bandit (LinUCB) — **start here** |
| Multi-step session | Q-learning / DQN |
| Historical claims only | Offline RL + IPS |
| Replace GraphRAG | **Do not** |

## Quick start

```bash
pip install -r requirements-ml.txt

python -m ml.fault_code_rl.train --algo bandit --episodes 600
python -m ml.fault_code_rl.train --algo q --episodes 1200 \
  --out notebooks/fault_code_rl_artifacts/q_policy.pt
python -m ml.fault_code_rl.train --algo dqn --episodes 400 \
  --out notebooks/fault_code_rl_artifacts/dqn_policy.pt

# Client GPU
python -m ml.fault_code_rl.train --algo dqn --require-cuda --episodes 800
```

## Related notebooks

- GAN lab: `fault_code_gan_synthetic_images.ipynb`
- Vision MLOps: `fault_code_vision_mlops_playbook.ipynb`
- Index: `README-fault-code-vision.md`
