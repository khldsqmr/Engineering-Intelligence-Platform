"""Independent AI evaluation and automated governance."""

import json
from typing import Literal

from backend.ai_intelligence.evaluation.evaluation_schema import (
    EvaluationOutcome,
    JudgeOutput,
)
from backend.ai_intelligence.evaluation.scoring import (
    EVALUATION_VERSION,
    calculate_evaluation_score,
    determine_approval_status,
)
from backend.ai_intelligence.prompts.intelligence_evaluator import (
    EVALUATOR_PROMPT_VERSION,
    EVALUATOR_SYSTEM_PROMPT,
)
from backend.ai_intelligence.providers.ollama import (
    LLMProviderError,
    OllamaProvider,
)
from backend.ai_intelligence.reasoning.intelligence_engine import (
    NarrativeDraft,
)


def evaluate_draft(
    draft: NarrativeDraft,
    provider: OllamaProvider,
    *,
    mode: Literal["narrative", "question"],
) -> EvaluationOutcome:
    """Evaluate a generated draft and determine reuse eligibility."""

    # 01. Mandatory deterministic validation gate.

    if not draft.validationPassed:
        return EvaluationOutcome(
            evaluationVersion=EVALUATION_VERSION,
            approvalStatus="REJECTED",
            deterministicValidationPassed=False,
            findings=list(draft.validationErrors),
        )

    # 02. Abstention is not reusable business intelligence.

    if draft.generation.output.status != "ANSWERED":
        return EvaluationOutcome(
            evaluationVersion=EVALUATION_VERSION,
            approvalStatus="REJECTED",
            deterministicValidationPassed=True,
            findings=["No reusable analytical narrative was generated."],
        )

    # Evaluate application-rendered factual reports deterministically.

    output = draft.generation.output

    if (
        mode == "narrative"
        and getattr(draft, "deterministicObservation", False)
        and output.narrative is not None
        and (output.hypothesis is None or getattr(draft, "deterministicHypothesis", False))
        and not output.alternativeExplanations
        and output.recommendedInvestigation is None
    ):
        return EvaluationOutcome(
            evaluationVersion=EVALUATION_VERSION,
            approvalStatus="AUTO_APPROVED",
            evaluationScore=100.0,
            deterministicValidationPassed=True,
            eligibleForHistoricalContext=True,
            evaluatorModel="deterministic-report",
            evaluatorPromptVersion="deterministic-report.2",
            evaluatorLatencySeconds=0.0,
            findings=[
                "Application-rendered report passed deterministic "
                "validation. "
                + (
                    "Hypothesis rendered from a supported evidence pattern."
                    if output.hypothesis is not None
                    else "No hypothesis was included."
                )
            ],
        )

    # 03. Assemble independent evaluation context.

    evaluation_input = json.dumps(
        {
            "analyticalContext": json.loads(draft.modelInputJson),
            "candidate": (draft.generation.output.model_dump()),
        },
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    )

    # 04. Invoke the evaluator.

    try:
        result = provider.generate(
            system_prompt=EVALUATOR_SYSTEM_PROMPT,
            user_prompt=evaluation_input,
            response_schema=JudgeOutput,
            max_output_tokens=500,
        )

    except LLMProviderError:
        return EvaluationOutcome(
            evaluationVersion=EVALUATION_VERSION,
            approvalStatus="EVALUATION_FAILED",
            deterministicValidationPassed=True,
            evaluatorPromptVersion=EVALUATOR_PROMPT_VERSION,
            findings=["The evaluator did not return a valid response."],
        )

    # 05. Apply deterministic governance policy.

    judgment = result.output

    score = calculate_evaluation_score(judgment)

    decision = determine_approval_status(judgment)

    # Only proactive reports can become reusable business context.

    eligible = decision == "AUTO_APPROVED" and mode == "narrative"

    return EvaluationOutcome(
        evaluationVersion=EVALUATION_VERSION,
        approvalStatus=decision,
        evaluationScore=score,
        deterministicValidationPassed=True,
        eligibleForHistoricalContext=eligible,
        evaluatorModel=result.modelName,
        evaluatorPromptVersion=EVALUATOR_PROMPT_VERSION,
        evaluatorLatencySeconds=result.latencySeconds,
        judgeResult=judgment,
        findings=judgment.criticalErrors,
    )
