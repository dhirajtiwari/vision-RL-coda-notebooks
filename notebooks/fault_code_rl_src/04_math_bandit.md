## Part 2 — Mathematics: contextual bandits (next-best step)

When each decision is “pick one step now” with delayed outcome, a **contextual bandit** is enough:

\[
a_t = \pi(x_t), \quad r_t \sim R(\cdot \mid x_t, a_t)
\]

No long-horizon \(P(s'|s,a)\) model required.

### UCB1 (non-contextual)

\[
a_t = \arg\max_a \left( \hat\mu_a + c \sqrt{\frac{\ln t}{n_a}} \right)
\]

### LinUCB (contextual)

For context \(x \in \mathbb{R}^d\), per-arm ridge regression \(\hat\theta_a\):

\[
a_t = \arg\max_a \left( \hat\theta_a^\top x + \alpha \sqrt{x^\top A_a^{-1} x} \right)
\]

### Why bandits first for WarrantyGraph

- Maps cleanly onto “next CONFIRMS step”
- Exploration is controllable
- Works with sparse claim rewards
- CPU-only; no CUDA required
