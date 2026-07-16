env = DiagnosticMDP(seed=1)
logs = behavior_log_from_random_policy(env, n=800, seed=1)
print("logged decisions", len(logs), "example reward", round(logs[0].reward, 2))

# Target policy: always pick action 0 (filter) — IPS estimate
ips_always_0 = inverse_propensity_score(logs, target_actions=[0] * len(logs))
# Target = behavior clone
ips_behavior = inverse_propensity_score(logs, target_actions=[row.action for row in logs])
print("IPS always-arm0:", round(ips_always_0, 3))
print("IPS behavior-clone (should ~ mean reward):", round(ips_behavior, 3),
      "empirical mean", round(float(np.mean([r.reward for r in logs])), 3))

# Safety mask example: only graph-eligible steps for a drain-heavy case
eligible = [STEP_IDS.index(s) for s in ("s_filter", "s_hose", "s_pump", "s_escalate")]
mask = safety_mask_graph_eligible(len(STEP_IDS), eligible)
q_fake = np.array([0.1, 0.9, 0.2, 5.0, 0.3, 0.4, 0.0])  # inlet looks best raw
print("unmasked argmax", STEP_IDS[int(np.argmax(q_fake))])
print("masked argmax  ", STEP_IDS[masked_argmax(q_fake, mask)], "(eligible only)")

print("\nIntegration sketch:")
print(json.dumps(integration_sketch(), indent=2))
