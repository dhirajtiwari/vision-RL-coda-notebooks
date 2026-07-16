"""Reinforcement learning for warranty diagnostics decision policies.

Not a replacement for GraphRAG. Optional layer for:
  - next-best diagnostic step (contextual bandit / MDP)
  - escalation threshold tuning with delayed rewards
  - offline learning from historical claim outcomes

See notebooks/fault_code_rl_playbook.ipynb.
"""

from ml.fault_code_rl.device import device_report, pick_device

__all__ = ["device_report", "pick_device"]
