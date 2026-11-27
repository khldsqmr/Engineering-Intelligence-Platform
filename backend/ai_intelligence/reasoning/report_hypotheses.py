"""Conservative hypothesis patterns for weekly intelligence."""

from backend.ai_intelligence.context.context_schema import (
    IntelligenceContext,
)
from backend.ai_intelligence.reasoning.reasoning_schema import (
    EvidenceReference,
    RootCauseHypothesis,
)


def build_supported_hypothesis(
    context: IntelligenceContext,
    observed_metric_id: str,
) -> RootCauseHypothesis | None:
    """Return a qualified hypothesis only for supported patterns."""

    facts = {
        fact.metricId: fact
        for fact in context.analyticalContext
        if fact.currentValue is not None
        and fact.previousValue is not None
        and fact.direction != "UNAVAILABLE"
    }

    def matches(metric_id, direction):
        fact = facts.get(metric_id)
        return fact is not None and fact.direction == direction

    def reference(metric_id):
        fact = facts[metric_id]

        return EvidenceReference(
            evidenceRef=fact.evidenceRef,
            direction=fact.direction,
        )

    if (
        observed_metric_id == "medianMergeHours"
        and matches("medianMergeHours", "INCREASED")
        and matches("meanPreReviewHours", "INCREASED")
        and matches("preReviewTimeSharePct", "INCREASED")
        and matches("meanPostReviewHours", "DECREASED")
    ):
        return RootCauseHypothesis(
            text=(
                "Longer elapsed time before external review may "
                "be associated with slower merging. Shorter "
                "post-review duration suggests the observed "
                "slowdown is not uniform across lifecycle stages."
            ),
            supportingEvidence=[
                reference("medianMergeHours"),
                reference("meanPreReviewHours"),
                reference("preReviewTimeSharePct"),
            ],
            counterEvidence=[
                reference("meanPostReviewHours"),
            ],
        )

    return None
