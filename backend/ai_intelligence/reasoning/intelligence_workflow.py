"""Orchestrate narrative generation and automated evaluation."""

from dataclasses import dataclass

from backend.ai_intelligence.confidence.confidence import (
    HypothesisConfidence,
    calculate_confidence,
)
from backend.ai_intelligence.context.context_schema import (
    IntelligenceContext,
)
from backend.ai_intelligence.evaluation.evaluation_schema import (
    EvaluationOutcome,
)
from backend.ai_intelligence.evaluation.evaluator import (
    evaluate_draft,
)
from backend.ai_intelligence.providers.ollama import (
    LLMProviderError,
    OllamaProvider,
)
from backend.ai_intelligence.reasoning.intelligence_engine import (
    NarrativeDraft,
    generate_narrative,
)


@dataclass(frozen=True)
class IntelligenceResult:
    context: IntelligenceContext
    draft: NarrativeDraft | None
    evaluation: EvaluationOutcome
    confidence: HypothesisConfidence | None = None


def run_intelligence(
    context: IntelligenceContext,
    generator: OllamaProvider,
    evaluator: OllamaProvider,
    *,
    retry_feedback: tuple[str, ...] = (),
) -> IntelligenceResult:
    """Generate, validate and evaluate analytical intelligence."""

    try:
        draft = generate_narrative(
            context,
            generator,
            **({"retry_feedback": retry_feedback} if retry_feedback else {}),
        )

    except LLMProviderError:
        return IntelligenceResult(
            context=context,
            draft=None,
            evaluation=EvaluationOutcome(
                approvalStatus="REJECTED",
                deterministicValidationPassed=False,
                findings=["Generation failed to produce a valid response."],
            ),
        )

    evaluation = evaluate_draft(
        draft,
        evaluator,
        mode=context.userIntent.mode,
    )

    confidence = None

    hypothesis = draft.generation.output.hypothesis

    if evaluation.approvalStatus == "AUTO_APPROVED" and hypothesis is not None:
        confidence = calculate_confidence(
            hypothesis,
            context.analyticalContext,
            context.qualityContext.sourceCoverage,
        )

    return IntelligenceResult(
        context=context,
        draft=draft,
        evaluation=evaluation,
        confidence=confidence,
    )
