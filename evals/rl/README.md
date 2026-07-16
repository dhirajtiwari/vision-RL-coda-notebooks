# RL eval suite (diagnostic decision policies)

**Status:** scaffold + simulator gates.
**Rule:** RL may only re-rank **GraphRAG-eligible** diagnostic steps. Offline / shadow eval before canary.

## Run

```bash
# Train tabular Q + DQN (MPS/CUDA/CPU)
python -m ml.fault_code_rl.train --algo q --episodes 1200 \
  --out notebooks/fault_code_rl_artifacts/q_policy.pt

python -m ml.fault_code_rl.train --algo dqn --episodes 500 \
  --out notebooks/fault_code_rl_artifacts/dqn_policy.pt

# Eval vs random
python -m ml.fault_code_rl.eval_rl \
  --q-table notebooks/fault_code_rl_artifacts/q_policy.npz \
  --dqn notebooks/fault_code_rl_artifacts/dqn_policy.pt \
  --episodes 200 \
  --min-success-rate 0.35 \
  --report notebooks/fault_code_rl_artifacts/rl_eval.json
```

## Floors

See `evals/thresholds.yaml` → `rl_smoke` / `rl_full`.

## Related

- Playbook: `notebooks/fault_code_rl_playbook.ipynb`
- Package: `ml/fault_code_rl/`
- CUDA image: `docker/Dockerfile.ml` (shared with vision)
