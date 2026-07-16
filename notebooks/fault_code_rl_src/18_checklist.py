df = pd.DataFrame(mlops_checklist())
print(df.to_string(index=False))
df.to_csv(ART / "rl_mlops_checklist.csv", index=False)

# Show registry stubs
import yaml
reg = yaml.safe_load((ROOT / "models" / "registry.yaml").read_text())
rl_aliases = {k: v for k, v in reg["models"].items() if "diagnosis" in k or k.endswith("dqn") or "bandit" in k}
# filter rl-related
rl_aliases = {k: v for k, v in reg["models"].items() if k.startswith("diagnosis-")}
print("\nRegistry stubs:")
print(yaml.dump(rl_aliases, sort_keys=False))

summary = {
    "playbook": "notebooks/fault_code_rl_playbook.ipynb",
    "package": "ml/fault_code_rl",
    "recommended_first_algo": "contextual_bandit_LinUCB",
    "deep_rl_algo": "DQN_on_DiagnosticMDP",
    "cuda": "Required for DQN client trains; bandits/Q on CPU",
    "constraint": "action_mask=graph_eligible_CONFIRMS_only",
    "do_not": "replace_GraphRAG_with_unconstrained_RL",
}
(ART / "executive_summary.json").write_text(json.dumps(summary, indent=2))
print(json.dumps(summary, indent=2))
