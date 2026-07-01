"""Unit tests for the deterministic reliability / diagnosis scoring engine.

These tests are pure (no Neo4j) and assert the FMEA + naive-Bayes math is
deterministic and behaves according to the referenced standards.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from graph import reliability as rel


def test_severity_rating_takes_worst_case():
    assert rel.severity_rating(["low", "high", "medium"]) == rel.SEVERITY_SCALE["high"]
    assert rel.severity_rating(["critical"]) == 10
    assert rel.severity_rating([]) == 5  # default when unknown


def test_occurrence_rating_monotonic_in_evidence():
    ratings = [rel.occurrence_rating(n) for n in (0, 1, 3, 5, 10, 40)]
    assert ratings == sorted(ratings)  # never decreases with more field evidence
    assert rel.occurrence_rating(0) == 3
    assert rel.occurrence_rating(40) == 9


def test_detection_rating_improves_with_coverage():
    # More diagnostic coverage => lower (better) detection rating.
    assert rel.detection_rating(0, 0) > rel.detection_rating(2, 0)
    assert rel.detection_rating(4, 2) == 2


def test_rpn_is_product():
    assert rel.rpn(8, 5, 4) == 160
    assert rel.rpn(10, 9, 7) == 630


def test_action_priority_severity_dominates():
    # High severity with real occurrence => High priority regardless of RPN size.
    assert rel.action_priority(10, 5, 3) == "High"
    # Low severity, low occurrence, easy detection => Low priority.
    assert rel.action_priority(2, 2, 2) == "Low"


def test_bayesian_posteriors_normalise_to_one():
    priors = {"fm1": 0.5, "fm2": 0.5}
    likelihoods = {("s1", "fm1"): 0.9, ("s1", "fm2"): 0.2}
    post = rel.bayesian_posteriors(priors, likelihoods, ["s1"], ["fm1", "fm2"])
    assert abs(sum(post.values()) - 1.0) < 1e-9
    assert post["fm1"] > post["fm2"]  # stronger likelihood wins


def test_bayesian_prior_breaks_ties():
    # Equal likelihoods => the higher occurrence prior should lead.
    priors = {"fm1": 0.8, "fm2": 0.2}
    likelihoods = {("s1", "fm1"): 0.7, ("s1", "fm2"): 0.7}
    post = rel.bayesian_posteriors(priors, likelihoods, ["s1"], ["fm1", "fm2"])
    assert post["fm1"] > post["fm2"]


def test_bayesian_is_deterministic():
    priors = {"fm1": 0.4, "fm2": 0.6}
    likelihoods = {("s1", "fm1"): 0.9, ("s2", "fm2"): 0.8}
    args = (priors, likelihoods, ["s1", "s2"], ["fm1", "fm2"])
    assert rel.bayesian_posteriors(*args) == rel.bayesian_posteriors(*args)


def test_missing_likelihood_does_not_zero_out_candidate():
    priors = {"fm1": 0.5, "fm2": 0.5}
    # fm2 has no edge for s1 => uses miss likelihood, still positive.
    likelihoods = {("s1", "fm1"): 0.9}
    post = rel.bayesian_posteriors(priors, likelihoods, ["s1"], ["fm1", "fm2"])
    assert post["fm2"] > 0.0
    assert post["fm1"] > post["fm2"]


def test_no_candidates_returns_empty():
    assert rel.bayesian_posteriors({}, {}, ["s1"], []) == {}


def test_end_to_end_diagnostic_scenario():
    """Two symptoms, three failure modes: the mode explaining both wins."""
    priors = {fm: rel.occurrence_prior(5) for fm in ("fm1", "fm2", "fm3")}
    likelihoods = {
        ("spin", "fm1"): 0.92,
        ("water", "fm1"): 0.60,
        ("water", "fm2"): 0.88,
        ("noise", "fm3"): 0.85,
    }
    post = rel.bayesian_posteriors(priors, likelihoods, ["spin", "water"], ["fm1", "fm2", "fm3"])
    assert max(post, key=post.get) == "fm1"
    assert post["fm3"] == min(post.values())
