## Part 0 — Which RL for *this* project?

| Need | RL family | Why it fits warranty diagnostics | Hardware |
|------|-----------|----------------------------------|----------|
| Next diagnostic step / question | **Contextual bandit** (LinUCB, Thompson) | Partial feedback; one action per decision; safer | CPU |
| Multi-step session (tests in sequence) | **MDP + Q-learning / DQN** | State = evidence so far; delayed resolve reward | Q: CPU; DQN: **CUDA** preferred |
| Learn only from historical claims | **Offline / batch RL + IPS** | No live random exploration on customers | CPU / CUDA for deep models |
| Escalation vs self-serve cost | Bandit or constrained MDP | Explicit cost-sensitive rewards | CPU |
| Replace GraphRAG | **Avoid** | Audit, safety, sparse/noisy rewards | — |

### Recommended adoption order (client roadmap)

1. **Log** (context, suggested step, outcome, propensity)
2. **Contextual bandit** in **shadow mode** (log only)
3. **Offline eval** (IPS) → canary
4. **MDP/DQN** only when multi-turn sessions + enough data

Authoritative algorithms in this notebook: UCB1 (Auer et al.), LinUCB (Li et al. 2010), Q-learning (Watkins; Sutton & Barto), DQN (Mnih et al. 2015).
