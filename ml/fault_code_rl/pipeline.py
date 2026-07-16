"""Orchestration + client MLOps checklist for diagnostic RL."""

from __future__ import annotations

from typing import Any


def rl_when_needed() -> list[dict[str, str]]:
    return [
        {
            "use_case": "Next-best diagnostic step ranking",
            "rl_type": "Contextual bandit (LinUCB / Thompson)",
            "why": "Partial feedback from agent/customer outcomes; safer than full RL",
            "priority": "P0 if personalizing step order beyond static CONFIRMS",
        },
        {
            "use_case": "Sequential test selection (multi-step session)",
            "rl_type": "MDP + Q-learning or DQN",
            "why": "State = evidence so far; action = next step; delayed resolution reward",
            "priority": "P1 when sessions are multi-turn and logged",
        },
        {
            "use_case": "Escalation threshold / cost-sensitive resolve",
            "rl_type": "Contextual bandit or constrained MDP",
            "why": "Trade accuracy vs field-tech cost under delayed claim outcome",
            "priority": "P1",
        },
        {
            "use_case": "Learn from historical claims only (no live explore)",
            "rl_type": "Offline / batch RL + IPS evaluation",
            "why": "Enterprise cannot randomly explore bad repairs on customers",
            "priority": "P0 for production learning loop",
        },
        {
            "use_case": "OCR model selection / cascade (vision+RL)",
            "rl_type": "Bandit over model versions",
            "why": "Route easy/hard images to cheap vs expensive OCR",
            "priority": "P2",
        },
        {
            "use_case": "Replace GraphRAG reasoning with RL",
            "rl_type": "Not recommended",
            "why": "Auditability, safety, sparse rewards — keep deterministic core",
            "priority": "Avoid",
        },
    ]


def mlops_checklist() -> list[dict[str, Any]]:
    return [
        {"phase": 0, "item": "Charter: RL re-ranks graph-eligible actions only (constraint)", "status": "required"},
        {"phase": 0, "item": "Define reward from claim outcomes (resolved, cost, reopen, CSAT)", "status": "required"},
        {
            "phase": 1,
            "item": "CUDA env for DQN (same Dockerfile.ml / device_report as vision)",
            "status": "recommended",
        },
        {"phase": 1, "item": "Bandits can train on CPU — no GPU required", "status": "info"},
        {"phase": 2, "item": "Logging: context, action, propensity, reward, model_version", "status": "required"},
        {"phase": 3, "item": "Offline eval (IPS/DR) before online canary", "status": "required"},
        {"phase": 3, "item": "Shadow mode: log RL action, serve GraphRAG action", "status": "required"},
        {"phase": 4, "item": "Registry pin diagnosis-step-policy / dqn-policy", "status": "required"},
        {"phase": 4, "item": "Canary % sessions + rollback alias", "status": "required"},
        {"phase": 5, "item": "Safety: never invent ErrorCodes or skip mandatory safety steps", "status": "required"},
        {"phase": 5, "item": "Human escalate always available as action", "status": "required"},
        {"phase": 6, "item": "Monitor regret proxy, success rate, cost/session, drift", "status": "required"},
    ]


def integration_sketch() -> dict[str, Any]:
    return {
        "runtime_flow": [
            "GraphRAG ranks failure modes + candidate CONFIRMS steps (eligible set)",
            "RL policy re-orders / selects next step among eligible only",
            "Agent/customer outcome logged as reward (delayed OK)",
            "Offline update → eval → registry pin → canary",
        ],
        "graph_hooks": [
            "graph.graph_rag rank_failure_modes / get_diagnostic_steps",
            "CONFIRMS edges define eligible action mask",
            "HistoricalResolution / claims outcomes → reward labels",
        ],
        "not_in_scope_v1": [
            "End-to-end RL replacing Neo4j path",
            "Unconstrained exploration on live warranty payouts",
        ],
    }
