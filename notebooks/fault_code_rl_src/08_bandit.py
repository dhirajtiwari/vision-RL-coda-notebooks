N = 600
d = len(DiagnosticMDP(seed=0).context.feature_vector())
curves = {}
final = {}
for name, make, contextual in [
    ("epsilon_greedy", lambda: EpsilonGreedy(len(STEP_IDS), epsilon=0.1, seed=0), False),
    ("ucb1", lambda: UCB1(len(STEP_IDS), c=1.5), False),
    ("thompson", lambda: ThompsonSampling(len(STEP_IDS), seed=0), False),
    ("linucb", lambda: LinUCB(len(STEP_IDS), d=d, alpha=0.5), True),
]:
    env = DiagnosticMDP(seed=0)
    out = run_bandit_on_mdp(env, make(), n_episodes=N, contextual=contextual)
    curves[name] = out["curve"]
    final[name] = out["mean_return"]
    print(f"{name:16s} mean_return={out['mean_return']:.3f}")

fig, ax = plt.subplots(figsize=(9, 4))
for name, c in curves.items():
    ax.plot(c, label=name, alpha=0.9)
ax.set_xlabel("episode")
ax.set_ylabel("avg return so far")
ax.set_title("Bandit learning curves (first-step policy on DiagnosticMDP)")
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(ART / "bandit_curves.png", dpi=120)
plt.show()
(ART / "bandit_results.json").write_text(json.dumps(final, indent=2))
