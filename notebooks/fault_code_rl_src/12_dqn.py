dqn_cfg = DQNConfig(episodes=400, seed=42, require_cuda=False)  # True on client NVIDIA
dqn_result = train_dqn(dqn_cfg)
print("device:", dqn_result["device"])
print("mean return last 100:", dqn_result["mean_return_last_100"])

fig, ax = plt.subplots(1, 2, figsize=(10, 3.5))
# smooth returns
w = 20
ret = np.array(dqn_result["returns"])
smooth = np.convolve(ret, np.ones(w)/w, mode="valid")
ax[0].plot(smooth)
ax[0].set_title("DQN episode return (smoothed)")
ax[0].grid(True, alpha=0.3)
if dqn_result["losses"]:
    ax[1].plot(dqn_result["losses"][:: max(1, len(dqn_result["losses"])//500)])
    ax[1].set_title("DQN TD loss (subsampled)")
    ax[1].grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(ART / "dqn_curves.png", dpi=120)
plt.show()

ckpt = ART / "dqn_policy.pt"
torch.save(
    {
        "policy": dqn_result["policy"].state_dict(),
        "obs_dim": dqn_result["obs_dim"],
        "n_actions": dqn_result["n_actions"],
        "steps": STEP_IDS,
        "device_report": dqn_result["device_report"],
    },
    ckpt,
)
print("saved", ckpt)
