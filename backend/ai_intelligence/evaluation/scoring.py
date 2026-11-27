"""Deterministic evaluation scoring and approval policy."""

from backend.ai_intelligence.evaluation.evaluation_schema import (
    JudgeOutput,
)

EVALUATION_VERSION = "1.0.0"

EVALUATION_WEIGHTS = {
    "factualConsistency": 30,
    "evidenceGrounding": 25,
    "analyticalReasoning": 20,
    "counterEvidence": 10,
    "uncertaintyHandling": 10,
    "businessRelevance": 5,
}

APPROVAL_THRESHOLD = 85
REGENERATION_THRESHOLD = 65
CRITICAL_REJECTION_THRESHOLD = 70
CRITICAL_APPROVAL_THRESHOLD = 90


def calculate_evaluation_score(
    judgment: JudgeOutput,
) -> float:

    scores = judgment.scores.model_dump()

    return round(
        sum(scores[criterion] * weight for criterion, weight in EVALUATION_WEIGHTS.items()) / 100,
        2,
    )


def determine_approval_status(
    judgment: JudgeOutput,
):
    score = calculate_evaluation_score(judgment)

    factual = judgment.scores.factualConsistency
    grounding = judgment.scores.evidenceGrounding

    if judgment.criticalErrors:
        return "REJECTED"

    if min(factual, grounding) < CRITICAL_REJECTION_THRESHOLD:
        return "REJECTED"

    if (
        score >= APPROVAL_THRESHOLD
        and factual >= CRITICAL_APPROVAL_THRESHOLD
        and grounding >= CRITICAL_APPROVAL_THRESHOLD
    ):
        return "AUTO_APPROVED"

    if score >= REGENERATION_THRESHOLD:
        return "REGENERATE"

    return "REJECTED"
