"""
FinOps package (kickoff prompt §F, handbook ch06).

Token/cost metering hooks live in observability.metrics; this package adds
BUDGET enforcement + a circuit breaker for the optional LLM path. Inactive while
the deterministic core is the only path, but ready to guard spend the moment the
gateway is switched on.
"""

from finops.budget import BudgetExceeded, DailyCostBudget

__all__ = ["DailyCostBudget", "BudgetExceeded"]
