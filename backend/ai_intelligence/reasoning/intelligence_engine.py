"""Connect structured analytical context to LLM reasoning."""

import json
from dataclasses import dataclass

from backend.ai_intelligence.context.context_schema import (
    IntelligenceContext,
)
from backend.ai_intelligence.prompts.engineering_analyst import (
    PROMPT_VERSION,
    SYSTEM_PROMPT,
)
from backend.ai_intelligence.providers.ollama import (
    GenerationResult,
    OllamaProvider,
)
from backend.ai_intelligence.reasoning.reasoning_schema import (
    NarrativeOutput,
)
from backend.ai_intelligence.validation.evidence_validator import (
    validate_evidence,
)


@dataclass(frozen=True)
class NarrativeDraft:
    generation: GenerationResult[NarrativeOutput]
    promptVersion: str
    modelInputJson: str
    validationErrors: tuple[str, ...]

    @property
    def validationPassed(self) -> bool:
        return not self.validationErrors


def prepare_model_context(
    context: IntelligenceContext,
) -> dict:
    """Build a compact analytical context for model inference."""

    semantics = {metric.metricId: metric for metric in context.semanticContext}

    def rounded(value):
        return round(value, 2) if value is not None else None

    facts = []

    for fact in context.analyticalContext:
        definition = semantics[fact.metricId]

        facts.append(
            [
                fact.evidenceRef,
                fact.metricId,
                definition.metricName,
                definition.metricUnit,
                definition.analyticalCohort,
                rounded(fact.previousValue),
                rounded(fact.currentValue),
                rounded(fact.changePct),
                fact.direction,
                rounded(fact.changeVsBenchmarkPct),
                fact.benchmarkPeriodCount,
                fact.previousSampleSize,
                fact.sampleSize,
                rounded(fact.previousEnrichmentCoveragePct),
                rounded(fact.enrichmentCoveragePct),
                fact.previousCoverageStatus,
                fact.coverageStatus,
                definition.calculationDefinition,
                definition.interpretationGuidance,
            ]
        )

    return {
        "contextVersion": context.contextVersion,
        "projectionVersion": "1.1.0",
        "repository": context.repository,
        "period": context.temporalContext.model_dump(),
        "factColumns": [
            "evidenceRef",
            "metricId",
            "metricName",
            "unit",
            "cohort",
            "previous",
            "current",
            "changePct",
            "direction",
            "changeVsBenchmarkPct",
            "benchmarkPeriodCount",
            "previousSampleSize",
            "sampleSize",
            "previousEnrichmentCoveragePct",
            "enrichmentCoveragePct",
            "previousCoverageStatus",
            "coverageStatus",
            "definition",
            "interpretation",
        ],
        "facts": facts,
        "relationships": [
            {
                "metrics": relationship.metricIds,
                "rule": relationship.interpretation,
            }
            for relationship in context.relationalContext
        ],
        "quality": context.qualityContext.model_dump(),
        "intent": context.userIntent.model_dump(),
        "historicalContext": [item.model_dump() for item in context.historicalContext],
    }


def generate_narrative(
    context: IntelligenceContext,
    provider: OllamaProvider,
) -> NarrativeDraft:
    """Generate compact intelligence and validate expanded claims."""

    from backend.ai_intelligence.providers.ollama import (
        LLMInvalidResponseError,
    )
    from backend.ai_intelligence.reasoning.compact_schema import (
        CompactNarrativeOutput,
        expand_output,
    )

    model_input = json.dumps(
        prepare_model_context(context),
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    )

    compact_generation = provider.generate(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=model_input,
        response_schema=CompactNarrativeOutput,
        max_output_tokens=650,
    )

    try:
        output = expand_output(compact_generation.output)

    except ValueError as exc:
        raise LLMInvalidResponseError("Compact response failed application validation.") from exc

    generation = GenerationResult(
        output=output,
        modelName=compact_generation.modelName,
        latencySeconds=compact_generation.latencySeconds,
        inputTokens=compact_generation.inputTokens,
        outputTokens=compact_generation.outputTokens,
    )

    errors = validate_evidence(
        generation.output,
        context.analyticalContext,
    )

    return NarrativeDraft(
        generation=generation,
        promptVersion=PROMPT_VERSION,
        modelInputJson=model_input,
        validationErrors=tuple(errors),
    )
