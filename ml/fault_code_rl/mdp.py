"""Diagnostic Markov Decision Process simulator.

State: bitmask of steps already performed + context embedding index
Action: choose next diagnostic step (including escalate)
Transition: step reveals positive/negative evidence toward hidden true FM
Reward: see rewards.py

This is a *simulator* for learning & demos. Production would log real outcomes
and train offline (batch RL) with safety constraints.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any

import numpy as np

from ml.fault_code_rl.domain import (
    ERROR_CODE_PRIOR,
    FAILURE_MODES,
    N_STEPS,
    STEP_INDEX,
    STEPS,
    EpisodeContext,
)
from ml.fault_code_rl.rewards import DEFAULT_REWARD, RewardConfig, step_reward, terminal_reward


@dataclass
class Transition:
    state: int
    action: int
    reward: float
    next_state: int
    done: bool
    info: dict[str, Any]


class DiagnosticMDP:
    """Finite-horizon diagnostic session with hidden true failure mode."""

    def __init__(
        self,
        max_steps: int = 4,
        reward_cfg: RewardConfig = DEFAULT_REWARD,
        seed: int | None = 42,
    ):
        self.max_steps = max_steps
        self.reward_cfg = reward_cfg
        self.rng = random.Random(seed)
        self.n_actions = N_STEPS
        # state = bitfield of performed steps (2^N_STEPS) — small N
        self.n_states = 1 << N_STEPS
        self.reset()

    def sample_context_and_truth(self) -> tuple[EpisodeContext, str]:
        code = self.rng.choice(list(ERROR_CODE_PRIOR.keys()))
        priors = ERROR_CODE_PRIOR[code]
        fms = list(priors.keys())
        weights = [priors[f] for f in fms]
        true_fm = self.rng.choices(fms, weights=weights, k=1)[0]
        symptoms = {
            "water_left": 1 if true_fm == "fm_drain" and self.rng.random() < 0.7 else 0,
            "noise": 1 if true_fm == "fm_balance" and self.rng.random() < 0.6 else 0,
            "no_spin": 1 if true_fm in {"fm_drain", "fm_door"} and self.rng.random() < 0.5 else 0,
            "door_ajar": 1 if true_fm == "fm_door" and self.rng.random() < 0.7 else 0,
        }
        ctx = EpisodeContext(error_code=code, symptom_flags=symptoms)
        return ctx, true_fm

    def reset(self, context: EpisodeContext | None = None, true_fm: str | None = None) -> int:
        if context is None or true_fm is None:
            context, true_fm = self.sample_context_and_truth()
        self.context = context
        self.true_fm = true_fm
        self.done_mask = 0  # bits of steps done
        self.t = 0
        self.positive_hits = 0
        self.escalated = False
        self.resolved = False
        return self.done_mask

    def _step_confirms_truth(self, step_id: str) -> bool:
        fm = next(f for f in FAILURE_MODES if f.fm_id == self.true_fm)
        # noisy confirmation
        if step_id in fm.confirming_steps:
            return self.rng.random() < 0.85
        return self.rng.random() < 0.12  # false positive rate

    def step(self, action: int) -> Transition:
        assert 0 <= action < self.n_actions
        step = STEPS[action]
        step_id = step.step_id
        info: dict[str, Any] = {"step_id": step_id, "true_fm": self.true_fm}

        # already done → small penalty, no progress
        if self.done_mask & (1 << action):
            r = -0.5
            self.t += 1
            done = self.t >= self.max_steps
            return Transition(self.done_mask, action, r, self.done_mask, done, info)

        self.done_mask |= 1 << action
        r = step_reward(step.cost, self.reward_cfg)
        self.t += 1

        if step_id == "s_escalate":
            self.escalated = True
            needed = self.true_fm in {"fm_door", "fm_drain"} and self.positive_hits < 1
            # escalate ends episode
            success = needed  # simplistic: escalate correct if hard case under-confirmed
            r += terminal_reward(
                success=success,
                escalated=True,
                escalation_was_needed=needed,
                cfg=self.reward_cfg,
            )
            info["success"] = success
            return Transition(self.done_mask, action, r, self.done_mask, True, info)

        hit = self._step_confirms_truth(step_id)
        info["evidence_positive"] = hit
        if hit:
            self.positive_hits += 1
            r += 1.5  # informative step

        # auto-resolve if enough confirming evidence for true FM
        fm = next(f for f in FAILURE_MODES if f.fm_id == self.true_fm)
        confirms_done = sum(1 for s in fm.confirming_steps if self.done_mask & (1 << STEP_INDEX[s]))
        if confirms_done >= min(2, len(fm.confirming_steps)) and hit:
            self.resolved = True
            r += terminal_reward(success=True, escalated=False, escalation_was_needed=False, cfg=self.reward_cfg)
            info["success"] = True
            return Transition(self.done_mask, action, r, self.done_mask, True, info)

        done = self.t >= self.max_steps
        if done and not self.resolved:
            r += terminal_reward(success=False, escalated=False, escalation_was_needed=False, cfg=self.reward_cfg)
            info["success"] = False
        return Transition(self.done_mask, action, r, self.done_mask, done, info)

    def encode_state_features(self, state_mask: int | None = None) -> np.ndarray:
        """Feature vector for DQN: step bitmask + context features."""
        mask = self.done_mask if state_mask is None else state_mask
        bits = [(mask >> i) & 1 for i in range(N_STEPS)]
        ctx = self.context.feature_vector()
        return np.asarray(bits + ctx, dtype=np.float32)
