from ml.fault_code_rl.eval_rl import evaluate_random, evaluate_q_table, evaluate_dqn_ckpt

env = DiagnosticMDP(seed=99)
rnd = evaluate_random(env, n=150, seed=2)
qmet = evaluate_q_table(q_result["Q"], DiagnosticMDP(seed=99), n=150)
dmet = evaluate_dqn_ckpt(ART / "dqn_policy.pt", DiagnosticMDP(seed=99), n=150)

report = {"random": rnd, "q_learning": qmet, "dqn": dmet}
print(json.dumps(report, indent=2))
(ART / "rl_eval_report.json").write_text(json.dumps(report, indent=2))

# simple smoke gate: at least one learned policy beats random success rate
delta_q = qmet["success_rate"] - rnd["success_rate"]
delta_d = dmet["success_rate"] - rnd["success_rate"]
print(f"Δ success Q={delta_q:+.3f} DQN={delta_d:+.3f}")
ok = max(delta_q, delta_d) >= 0.0  # weak smoke; tighten for client
print("SMOKE GATE:", "PASS" if ok else "FAIL (train longer)")
