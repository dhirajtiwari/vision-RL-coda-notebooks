from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

ROOT = Path(".").resolve()
if not (ROOT / "ml").is_dir():
    if (ROOT.parent / "ml").is_dir():
        ROOT = ROOT.parent
sys.path.insert(0, str(ROOT))

from ml.fault_code_rl.device import device_report, pick_device
from ml.fault_code_rl.domain import STEP_IDS, FAILURE_MODES, ERROR_CODE_PRIOR
from ml.fault_code_rl.mdp import DiagnosticMDP
from ml.fault_code_rl.bandits import EpsilonGreedy, UCB1, LinUCB, ThompsonSampling, run_bandit_on_mdp
from ml.fault_code_rl.q_learning import QLearningConfig, train_q_learning, greedy_policy_steps
from ml.fault_code_rl.dqn import DQNConfig, train_dqn, dqn_act
from ml.fault_code_rl.offline import behavior_log_from_random_policy, inverse_propensity_score, safety_mask_graph_eligible, masked_argmax
from ml.fault_code_rl.pipeline import rl_when_needed, mlops_checklist, integration_sketch
from ml.fault_code_rl.rewards import DEFAULT_REWARD
import pandas as pd
import torch

ART = ROOT / "notebooks" / "fault_code_rl_artifacts"
ART.mkdir(parents=True, exist_ok=True)

print("ROOT", ROOT)
print("device_report:", json.dumps(device_report(), indent=2))
print("device", pick_device())
print("Actions (diagnostic steps):", STEP_IDS)
print("Failure modes:", [f.fm_id for f in FAILURE_MODES])
print("Reward config:", DEFAULT_REWARD)
