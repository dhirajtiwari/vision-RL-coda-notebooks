env = DiagnosticMDP(max_steps=4, seed=7)
s = env.reset()
print("context error_code=", env.context.error_code, "true_fm=", env.true_fm)
print("symptoms", env.context.symptom_flags)
print("feature dim", len(env.encode_state_features()))

# manual short episode
done = False
total = 0.0
trace = []
while not done:
    # naive: prefer filter then hose then pump
    prefer = ["s_filter", "s_hose", "s_pump", "s_balance", "s_inlet", "s_door", "s_escalate"]
    a = next(STEP_IDS.index(x) for x in prefer if not (env.done_mask & (1 << STEP_IDS.index(x))))
    tr = env.step(a)
    total += tr.reward
    trace.append((STEP_IDS[a], round(tr.reward, 2), tr.info.get("evidence_positive"), tr.info.get("success")))
    done = tr.done
print("trace:", trace)
print("episode return", round(total, 2))

print("\nWhen is RL needed? (from package)")
display_df = pd.DataFrame(rl_when_needed())
print(display_df.to_string(index=False))
