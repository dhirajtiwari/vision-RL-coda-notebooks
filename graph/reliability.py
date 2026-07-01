"""
Reliability-engineering scoring for deterministic diagnosis.

This module replaces the previous hand-tuned magic constants with two
well-established, *deterministic* methods so that every number the system
reports can be traced to a recognised industry standard.

1. FMEA / FMECA — MIL-STD-1629A; SAE J1739; AIAG-VDA FMEA Handbook (2019).
   Each failure mode is characterised on ordinal 1-10 scales by:
       - Severity (S)   : consequence of the failure
       - Occurrence (O) : how often the cause/failure is expected
       - Detection (D)  : likelihood the failure is *missed* before impact
   The classic Risk Priority Number is RPN = S * O * D. Because multiplying
   ordinal ratings can cause rank reversals (Kmenta & Ishii, 2004), the
   AIAG-VDA 2019 handbook replaced RPN as the primary triage with an
   Action Priority (High/Medium/Low). We expose both: RPN for continuity and
   Action Priority as the recommended triage signal.

2. Naive-Bayes diagnostic inference — Pearl (1988); Russell & Norvig, AIMA.
   Given a set of observed symptoms S, the posterior probability of each
   candidate failure mode is

       P(fm | S)  ∝  P(fm) * ∏_i P(s_i | fm)

   normalised across the candidate failure modes so the posteriors form a
   proper probability distribution that sums to 1. Here:
       - P(fm)      (prior/occurrence) is derived from the FMEA Occurrence
                    rating, which is itself grounded in *observed* field
                    evidence (claim / resolution frequency) — an empirical
                    prior rather than a hand-typed constant.
       - P(s_i|fm)  (likelihood) is the confidence stored on the
                    (Symptom)-[:INDICATES]->(FailureMode) edge.

Every function here is pure and free of I/O so the scoring is unit-testable
and independent of Neo4j, and identical inputs always yield identical outputs.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence

# --- FMEA rating scales -----------------------------------------------------

# Severity (S): map catalog symptom severity labels onto the 1-10 FMEA scale.
# Anchored to the AIAG-VDA / MIL-STD severity bands.
SEVERITY_SCALE: dict[str, int] = {
    "critical": 10,
    "high": 8,
    "medium": 5,
    "low": 2,
}
_DEFAULT_SEVERITY = 5

# Probability of a symptom under a failure mode that does NOT list it as an
# indication (naive-Bayes "miss" likelihood). Kept away from 0 so a single
# unmatched symptom cannot zero out an otherwise strong candidate — this also
# satisfies the bounded-away-from-zero condition for stable inference
# (Dagum & Luby, 1997).
DEFAULT_MISS_LIKELIHOOD = 0.15


def severity_rating(severities: Iterable[str]) -> int:
    """FMEA Severity (1-10) = worst-case severity across a mode's symptoms."""
    ratings = [SEVERITY_SCALE.get((s or "").lower(), _DEFAULT_SEVERITY) for s in severities]
    return max(ratings) if ratings else _DEFAULT_SEVERITY


def occurrence_rating(evidence_count: int) -> int:
    """
    FMEA Occurrence (1-10) from *observed* field evidence.

    `evidence_count` is the number of historical confirmations of the failure
    mode (closed claims + technician resolutions). More confirmed occurrences
    ⇒ higher occurrence rating. Absence of field data is treated as low-but-not-
    impossible occurrence rather than "never".
    """
    n = max(int(evidence_count), 0)
    if n == 0:
        return 3
    if n <= 2:
        return 5
    if n <= 4:
        return 6
    if n <= 8:
        return 7
    if n <= 15:
        return 8
    return 9


def detection_rating(diagnostic_step_count: int, error_code_count: int = 0) -> int:
    """
    FMEA Detection (1-10). Higher rating = harder to detect before impact.

    Detection improves (rating drops) with diagnostic coverage: the number of
    diagnostic steps that confirm the mode plus any machine-reported error
    codes. This grounds Detection in the actual diagnostic assets in the graph.
    """
    coverage = max(int(diagnostic_step_count), 0) + max(int(error_code_count), 0)
    if coverage == 0:
        return 7
    if coverage == 1:
        return 5
    if coverage == 2:
        return 4
    if coverage == 3:
        return 3
    return 2


def rpn(severity: int, occurrence: int, detection: int) -> int:
    """Classic FMEA Risk Priority Number = S * O * D (1..1000)."""
    return int(severity) * int(occurrence) * int(detection)


def _ap_high(s: int, o: int, d: int) -> bool:
    """Conditions that warrant a High action priority."""
    if s >= 9:
        return o >= 4 or d >= 6
    if s >= 7:
        return o >= 6 or (o >= 4 and d >= 5)
    if s >= 4:
        return o >= 7 and d >= 6
    return False


def _ap_medium(s: int, o: int, d: int) -> bool:
    """Conditions that warrant a Medium action priority (when not High)."""
    if s >= 9:
        return True
    if s >= 7:
        return o >= 3 or d >= 5
    if s >= 4:
        return o >= 4 or d >= 5
    return o >= 8 and d >= 7


def action_priority(severity: int, occurrence: int, detection: int) -> str:
    """
    Action Priority (High/Medium/Low).

    A deterministic approximation of the AIAG-VDA 2019 Action Priority logic
    (the full published AP table is proprietary). Severity dominates, then
    Occurrence, then Detection — matching the handbook's ordering and avoiding
    the ordinal-multiplication rank-reversal problem of raw RPN.
    """
    s, o, d = int(severity), int(occurrence), int(detection)
    if _ap_high(s, o, d):
        return "High"
    if _ap_medium(s, o, d):
        return "Medium"
    return "Low"


def occurrence_prior(occurrence: int) -> float:
    """
    Convert an FMEA Occurrence rating (1-10) into a prior probability P(fm).

    The absolute value is unimportant because posteriors are normalised across
    candidates; only the *relative* ordering (more frequent ⇒ larger prior)
    matters. Kept strictly positive.
    """
    return max(int(occurrence), 1) / 10.0


def bayesian_posteriors(
    priors: Mapping[str, float],
    likelihoods: Mapping[tuple[str, str], float],
    observed_symptoms: Sequence[str],
    candidate_failure_modes: Sequence[str],
    *,
    miss_likelihood: float = DEFAULT_MISS_LIKELIHOOD,
) -> dict[str, float]:
    """
    Normalised naive-Bayes posterior P(fm | observed_symptoms).

    Args:
        priors: P(fm) per failure mode id.
        likelihoods: P(symptom | fm) keyed by (symptom_id, failure_mode_id);
            missing keys default to `miss_likelihood`.
        observed_symptoms: symptom ids treated as observed evidence.
        candidate_failure_modes: failure mode ids to score.
        miss_likelihood: P(symptom | fm) when no edge exists.

    Returns:
        {failure_mode_id: posterior} summing to 1.0 (or all-zeros if no signal).
    """
    if not candidate_failure_modes:
        return {}

    unnormalized: dict[str, float] = {}
    for fm in candidate_failure_modes:
        score = max(float(priors.get(fm, 0.0)), 0.0)
        for symptom in observed_symptoms:
            score *= float(likelihoods.get((symptom, fm), miss_likelihood))
        unnormalized[fm] = score

    total = sum(unnormalized.values())
    if total <= 0.0:
        return dict.fromkeys(candidate_failure_modes, 0.0)
    return {fm: score / total for fm, score in unnormalized.items()}
