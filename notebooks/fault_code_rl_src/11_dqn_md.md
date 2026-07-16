## Part 6 — Working code: DQN + CUDA/MPS (same hardware story as vision)

**Deep Q-Network** approximates \(Q(s,a;\theta)\) with a neural net (Mnih et al., Nature 2015):

- Replay buffer + target network
- ε-greedy exploration
- Trains on `pick_device()` → **CUDA** (client), **MPS** (Mac demo), or CPU

```bash
# Client GPU (shared image with vision)
docker build -f docker/Dockerfile.ml -t warrantygraph-ml:latest .
docker run --gpus all -v "$PWD":/workspace -w /workspace warrantygraph-ml:latest \
  python -m ml.fault_code_rl.train --algo dqn --episodes 800 --require-cuda \
  --out models/artifacts/rl/dqn.pt
```
