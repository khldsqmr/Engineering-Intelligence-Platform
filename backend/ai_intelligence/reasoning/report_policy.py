"""Evidence availability policy for weekly intelligence."""

from pydantic import Field, create_model

from backend.ai_intelligence.context.context_schema import (
    IntelligenceContext,
)
from backend.ai_intelligence.reasoning.compact_schema import (
    build_grounded_response_schema,
)


def observation_only_required(
    context: IntelligenceContext,
) -> bool:
    """Restrict reports when enrichment comparisons are unavailable."""

    enriched_metrics = {
        (metric.metricId, metric.metricVersion)
        for metric in context.semanticContext
        if (
            getattr(metric, "requiresDetailEnrichment", False)
            or getattr(metric, "requiresReviewEnrichment", False)
        )
    }

    if not enriched_metrics:
        return False

    comparable = any(
        (fact.metricId, fact.metricVersion) in enriched_metrics
        and fact.currentValue is not None
        and fact.previousValue is not None
        and fact.direction != "UNAVAILABLE"
        for fact in context.analyticalContext
    )

    return not comparable


def build_report_schema(context: IntelligenceContext):
    """Restrict unsupported interpretive fields at schema level."""

    schema = build_grounded_response_schema(
        context.analyticalContext,
        report_only=True,
    )

    if not observation_only_required(context):
        return schema

    return create_model(
        "ObservationOnlyReport",
        __base__=schema,
        hypothesis=(type(None), None),
        hypothesisRefs=(
            list[str],
            Field(default_factory=list, max_length=0),
        ),
        counterRefs=(
            list[str],
            Field(default_factory=list, max_length=0),
        ),
        alternative=(type(None), None),
        investigation=(type(None), None),
    )
