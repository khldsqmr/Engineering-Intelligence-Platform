"""Tests for evaluator integration and mandatory governance gates."""

from unittest.mock import Mock

import pytest

from backend.ai_intelligence.evaluation.evaluation_schema import (
    EvaluationScores,
    JudgeOutput,
)
from backend.ai_intelligence.evaluation.evaluator import (
    evaluate_draft,
)
from backend.ai_intelligence.providers.ollama import (
    GenerationResult,
    LLMUnavailableError,
    OllamaProvider,
)
from backend.ai_intelligence.reasoning.intelligence_engine import (
    NarrativeDraft,
)
from backend.ai_intelligence.reasoning.reasoning_schema import (
    NarrativeOutput,
)


def make_draft(errors=(), abstain=False):
    output = NarrativeOutput.model_validate(
        {
            "status": ("INSUFFICIENT_EVIDENCE" if abstain else "ANSWERED"),
            "narrative": None
            if abstain
            else {
                "text": "Initial review duration increased.",
                "supportingEvidence": [
                    {
                        "evidenceRef": "E07",
                        "direction": "INCREASED",
                    }
                ],
            },
            "hypothesis": None,
            "alternativeExplanations": [],
            "recommendedInvestigation": None,
        }
    )

    return NarrativeDraft(
        generation=GenerationResult(
            output=output,
            modelName="test-model",
            latencySeconds=1.0,
            inputTokens=100,
            outputTokens=50,
        ),
        promptVersion="1.3.0",
        modelInputJson='{"factColumns":[],"facts":[]}',
        validationErrors=errors,
    )


def make_evaluator(score=95, errors=None):
    provider = Mock(spec=OllamaProvider)

    judgment = JudgeOutput(
        scores=EvaluationScores(
            factualConsistency=score,
            evidenceGrounding=score,
            analyticalReasoning=score,
            counterEvidence=score,
            uncertaintyHandling=score,
            businessRelevance=score,
        ),
        criticalErrors=errors or [],
        explanation="Synthetic evaluator response.",
    )

    provider.generate.return_value = GenerationResult(
        output=judgment,
        modelName="test-evaluator",
        latencySeconds=1.0,
        inputTokens=100,
        outputTokens=50,
    )

    return provider


def test_invalid_draft_skips_evaluator():
    provider = make_evaluator()

    result = evaluate_draft(
        make_draft(errors=("Invalid evidence direction.",)),
        provider,
        mode="narrative",
    )

    assert result.approvalStatus == "REJECTED"
    assert result.eligibleForHistoricalContext is False
    provider.generate.assert_not_called()


def test_abstention_skips_evaluator():
    provider = make_evaluator()

    result = evaluate_draft(
        make_draft(abstain=True),
        provider,
        mode="question",
    )

    assert result.eligibleForHistoricalContext is False
    provider.generate.assert_not_called()


@pytest.mark.parametrize(
    ("mode", "eligible"),
    [
        ("narrative", True),
        ("question", False),
    ],
)
def test_approved_response_eligibility(mode, eligible):
    provider = make_evaluator()

    result = evaluate_draft(
        make_draft(),
        provider,
        mode=mode,
    )

    assert result.approvalStatus == "AUTO_APPROVED"
    assert result.evaluationScore == 95.0
    assert result.eligibleForHistoricalContext is eligible

    provider.generate.assert_called_once()


def test_critical_error_prevents_approval():
    provider = make_evaluator(
        score=99,
        errors=["Unsupported causal conclusion."],
    )

    result = evaluate_draft(
        make_draft(),
        provider,
        mode="narrative",
    )

    assert result.approvalStatus == "REJECTED"
    assert result.eligibleForHistoricalContext is False


def test_regeneration_does_not_allow_historical_reuse():
    provider = make_evaluator(score=80)

    result = evaluate_draft(
        make_draft(),
        provider,
        mode="narrative",
    )

    assert result.approvalStatus == "REGENERATE"
    assert result.eligibleForHistoricalContext is False


def test_evaluator_failure_is_fail_closed():
    provider = make_evaluator()

    provider.generate.side_effect = LLMUnavailableError("Evaluator unavailable.")

    result = evaluate_draft(
        make_draft(),
        provider,
        mode="narrative",
    )

    assert result.approvalStatus == "EVALUATION_FAILED"
    assert result.evaluationScore is None
    assert result.eligibleForHistoricalContext is False
