"""Ground generated numerical references in analytical context."""

from backend.ai_intelligence.context.context_schema import (
    IntelligenceContext,
)
from backend.ai_intelligence.numerical_grounding import (
    resolve_numerical_text,
)
from backend.ai_intelligence.reasoning.reasoning_schema import (
    NarrativeOutput,
)


def build_numerical_evidence(
    context: IntelligenceContext,
) -> dict[str, dict]:
    """Join analytical facts with governed metric units."""

    semantic_index = {(item.metricId, item.metricVersion): item for item in context.semanticContext}

    evidence = {}

    for fact in context.analyticalContext:
        semantic = semantic_index.get((fact.metricId, fact.metricVersion))

        if semantic is None:
            continue

        evidence[fact.evidenceRef] = {
            **fact.model_dump(mode="json"),
            "metricUnit": semantic.metricUnit,
        }

    return evidence


def resolve_output(
    output: NarrativeOutput,
    evidence: dict[str, dict],
) -> NarrativeOutput:
    """Produce a resolved copy without modifying the original template."""

    resolved = output.model_copy(deep=True)

    if resolved.narrative is not None:
        references = {item.evidenceRef for item in resolved.narrative.supportingEvidence}

        resolved.narrative.text = resolve_numerical_text(
            resolved.narrative.text,
            evidence=evidence,
            allowed_references=references,
        )

    if resolved.hypothesis is not None:
        references = {
            item.evidenceRef
            for item in (
                resolved.hypothesis.supportingEvidence + resolved.hypothesis.counterEvidence
            )
        }

        resolved.hypothesis.text = resolve_numerical_text(
            resolved.hypothesis.text,
            evidence=evidence,
            allowed_references=references,
        )

    # These fields do not have their own structured evidence references.
    # Keep them qualitative until their schema supports explicit citations.

    resolved.alternativeExplanations = [
        resolve_numerical_text(
            explanation,
            evidence=evidence,
            allowed_references=set(),
        )
        for explanation in resolved.alternativeExplanations
    ]

    if resolved.recommendedInvestigation is not None:
        resolved.recommendedInvestigation = resolve_numerical_text(
            resolved.recommendedInvestigation,
            evidence=evidence,
            allowed_references=set(),
        )

    return resolved
