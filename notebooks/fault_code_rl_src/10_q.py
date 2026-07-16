q_result = train_q_learning(cfg=QLearningConfig(episodes=1200, seed=42))
print("mean return last 100:", q_result["mean_return_last_100"])
print("success rate last 100:", q_result["success_rate_last_100"])

fig, ax = plt.subplots(figsize=(9, 3.5))
ax.plot(q_result["moving_avg_return"], color="steelblue")
ax.set_title("Q-learning moving average return (window=100)")
ax.set_xlabel("episode")
ax.set_ylabel("return")
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(ART / "q_learning_curve.png", dpi=120)
plt.show()

# Greedy action sequence from empty evidence
acts = greedy_policy_steps(q_result["agent"], state=0, max_steps=4)
print("Greedy steps from empty state:", [STEP_IDS[a] for a in acts])

np.savez(ART / "q_policy.npz", Q=q_result["Q"])
print("saved", ART / "q_policy.npz")
