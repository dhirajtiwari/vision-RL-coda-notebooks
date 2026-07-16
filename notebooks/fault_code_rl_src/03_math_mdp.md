## Part 1 — Mathematics: diagnosis as an MDP

A **Markov Decision Process** is \(\langle \mathcal{S}, \mathcal{A}, P, R, \gamma \rangle\).

| Symbol | In this product |
|--------|-----------------|
| State \(s \in \mathcal{S}\) | Evidence so far: steps done, product, error code, symptoms |
| Action \(a \in \mathcal{A}\) | Next diagnostic step / question / escalate |
| Transition \(P(s'|s,a)\) | Test outcome (pass/fail evidence) changes belief state |
| Reward \(R(s,a)\) | \(+\) resolve success, \(-\) step cost, \(-\) wrong path / reopen |
| Discount \(\gamma \in [0,1)\) | Prefer faster resolution |

### Objective

\[
\pi^\star = \arg\max_\pi \; \mathbb{E}_{\pi}\Big[\sum_{t=0}^{T} \gamma^t r_t\Big]
\]

### Bellman optimality (Q-function)

\[
Q^\star(s,a) = \mathbb{E}\big[r + \gamma \max_{a'} Q^\star(s',a') \mid s,a\big]
\]

**Tabular Q-learning update** (Watkins):

\[
Q(s,a) \leftarrow Q(s,a) + \alpha \big(r + \gamma \max_{a'} Q(s',a') - Q(s,a)\big)
\]

### Constraint (enterprise)

\[
a_t \in \mathcal{A}_{\text{eligible}}(s_t) \subseteq \text{GraphRAG CONFIRMS candidates}
\]

RL **must not** invent steps or codes outside the knowledge graph.
