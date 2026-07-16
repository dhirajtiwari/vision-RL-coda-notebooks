## Part 9 — CUDA & MLOps (aligned with vision stack)

| Concern | Vision (`fault_code_vision`) | RL (`fault_code_rl`) |
|---------|------------------------------|----------------------|
| Device helpers | `device_report`, `assert_cuda_for_client_train` | **Same** (re-exported) |
| GPU image | `docker/Dockerfile.ml` | **Same image** |
| Deps | `requirements-ml.txt` | **Same file** |
| Registry | `fault-code-ocr`, `fault-code-gan` | `diagnosis-step-bandit`, `diagnosis-session-dqn` |
| Eval floors | `vision_*` in `thresholds.yaml` | `rl_*` |
| Train CLI | `python -m ml.fault_code_vision.train_ocr` | `python -m ml.fault_code_rl.train` |

### Hardware guidance

| Algorithm | GPU needed? |
|-----------|-------------|
| Epsilon-greedy / UCB / Thompson / LinUCB | **No** (CPU) |
| Tabular Q-learning | **No** |
| DQN / future deep offline RL | **Yes (CUDA)** for client-scale train |

### Runtime integration (target)

```text
GraphRAG eligible steps ──► action mask
context (product, code, symptoms, steps_done)
        │
        ▼
  bandit / DQN policy (pinned registry alias)
        │
        ▼
  next step to agent UI
        │
        ▼
  outcome logger → offline train → eval → canary
```
