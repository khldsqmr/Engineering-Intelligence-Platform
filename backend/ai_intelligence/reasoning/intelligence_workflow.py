"""Orchestrate narrative generation and automated evaluation."""

from dataclasses import dataclass

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


def run_intelligence(
    context: IntelligenceContext,
    generator: OllamaProvider,
    evaluator: OllamaProvider,
) -> IntelligenceResult:
    """Generate, validate and evaluate analytical intelligence."""

    try:
        draft = generate_narrative(
            context,
            generator,
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

    return IntelligenceResult(
        context=context,
        draft=draft,
        evaluation=evaluation,
    )
