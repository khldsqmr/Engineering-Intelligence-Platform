"""Tests for deterministic AI approval policy."""

import pytest

from backend.ai_intelligence.evaluation.evaluation_schema import (
    EvaluationScores,
    JudgeOutput,
)
from backend.ai_intelligence.evaluation.scoring import (
    EVALUATION_WEIGHTS,
    calculate_evaluation_score,
    determine_approval_status,
)


def make_judgment(
    score,
    factual=None,
    grounding=None,
    errors=None,
):
    return JudgeOutput(
        scores=EvaluationScores(
            factualConsistency=(score if factual is None else factual),
            evidenceGrounding=(score if grounding is None else grounding),
            analyticalReasoning=score,
            counterEvidence=score,
            uncertaintyHandling=score,
            businessRelevance=score,
        ),
        criticalErrors=errors or [],
        explanation="Synthetic evaluation fixture.",
    )


def test_weights_sum_to_one_hundred():
    assert sum(EVALUATION_WEIGHTS.values()) == 100


def test_weighted_score():
    judgment = make_judgment(
        80,
        factual=100,
        grounding=100,
    )

    assert calculate_evaluation_score(judgment) == 91.0


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (95, "AUTO_APPROVED"),
        (85, "REGENERATE"),
        (75, "REGENERATE"),
        (65, "REJECTED"),
        (40, "REJECTED"),
    ],
)
def test_approval_thresholds(score, expected):
    assert determine_approval_status(make_judgment(score)) == expected


def test_critical_error_overrides_high_score():
    judgment = make_judgment(
        99,
        errors=["Incorrect metric interpretation"],
    )

    assert determine_approval_status(judgment) == "REJECTED"


def test_factual_score_below_minimum():
    judgment = make_judgment(
        95,
        factual=60,
    )

    assert determine_approval_status(judgment) == "REJECTED"


def test_grounding_below_approval_threshold():
    judgment = make_judgment(
        95,
        grounding=85,
    )

    assert determine_approval_status(judgment) == "REGENERATE"
