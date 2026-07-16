## Part 7 — Offline RL & safety (what clients actually need)

### Inverse Propensity Scoring (sketch)

Behavior policy \(\pi_b\) logged propensities \(\pi_b(a|x)\). For target \(\pi\):

\[
\hat V_{\mathrm{IPS}} = \frac{1}{N}\sum_{i=1}^{N} \frac{\mathbf{1}[a_i=\pi(x_i)]}{\pi_b(a_i|x_i)} r_i
\]

### Production pattern

1. **Shadow:** serve GraphRAG; log what RL *would* have done
2. **Offline IPS / DR** on logged data
3. **Canary** small %
4. **Action mask** = CONFIRMS-eligible steps only
