"""Domain model: sequential remote diagnosis as an MDP / bandit problem.

Aligned with WarrantyGraph concepts:
  Product + symptoms/error codes → ranked FailureMode → CONFIRMS DiagnosticSteps.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class FailureModeSpec:
    fm_id: str
    name: str
    # steps that truly confirm this FM (ground truth for simulator)
    confirming_steps: tuple[str, ...]
    prior: float = 0.25


@dataclass(frozen=True)
class StepSpec:
    step_id: str
    description: str
    cost: float = 1.0  # customer/agent effort units


# Compact demo world (washer-like) for client showcase — not full catalog.
STEPS: list[StepSpec] = [
    StepSpec("s_filter", "Clean / inspect drain filter", cost=1.0),
    StepSpec("s_hose", "Check drain hose for kinks/blockage", cost=1.0),
    StepSpec("s_pump", "Ohm-test / listen to drain pump", cost=2.0),
    StepSpec("s_inlet", "Verify water inlet taps and screens", cost=1.0),
    StepSpec("s_balance", "Redistribute load / rebalance drum", cost=0.5),
    StepSpec("s_door", "Inspect door lock / switch", cost=1.5),
    StepSpec("s_escalate", "Escalate to field technician", cost=5.0),
]

FAILURE_MODES: list[FailureModeSpec] = [
    FailureModeSpec(
        "fm_drain",
        "Drain path blocked / pump weak",
        confirming_steps=("s_filter", "s_hose", "s_pump"),
        prior=0.35,
    ),
    FailureModeSpec(
        "fm_inlet",
        "Inlet / fill insufficient",
        confirming_steps=("s_inlet",),
        prior=0.20,
    ),
    FailureModeSpec(
        "fm_balance",
        "Unbalanced load",
        confirming_steps=("s_balance",),
        prior=0.25,
    ),
    FailureModeSpec(
        "fm_door",
        "Door lock fault",
        confirming_steps=("s_door",),
        prior=0.20,
    ),
]

# Error-code → likely FM (mirrors INDICATES-style boosts)
ERROR_CODE_PRIOR: dict[str, dict[str, float]] = {
    "5E": {"fm_drain": 0.85, "fm_inlet": 0.05, "fm_balance": 0.05, "fm_door": 0.05},
    "UE": {"fm_balance": 0.80, "fm_drain": 0.10, "fm_inlet": 0.05, "fm_door": 0.05},
    "4E": {"fm_inlet": 0.75, "fm_drain": 0.10, "fm_balance": 0.10, "fm_door": 0.05},
    "DE": {"fm_door": 0.80, "fm_drain": 0.05, "fm_inlet": 0.05, "fm_balance": 0.10},
    "NONE": {fm.fm_id: fm.prior for fm in FAILURE_MODES},
}

STEP_IDS = [s.step_id for s in STEPS]
STEP_INDEX = {s: i for i, s in enumerate(STEP_IDS)}
FM_IDS = [f.fm_id for f in FAILURE_MODES]
FM_INDEX = {f: i for i, f in enumerate(FM_IDS)}
N_STEPS = len(STEP_IDS)
N_FMS = len(FM_IDS)


@dataclass
class EpisodeContext:
    """Observable context at session start (bandit / MDP context features)."""

    product_id: str = "wm-001"
    error_code: str = "NONE"
    symptom_flags: dict[str, int] = field(default_factory=dict)  # e.g. water_left=1

    def feature_vector(self) -> list[float]:
        """Fixed-length context for linear bandits / DQN."""
        # one-hot error codes we care about + simple symptoms
        codes = ["5E", "UE", "4E", "DE", "NONE"]
        x = [1.0 if self.error_code == c else 0.0 for c in codes]
        for key in ("water_left", "noise", "no_spin", "door_ajar"):
            x.append(float(self.symptom_flags.get(key, 0)))
        return x
