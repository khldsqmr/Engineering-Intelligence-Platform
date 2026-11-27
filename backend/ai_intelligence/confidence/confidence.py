"""Deterministic evidence-strength scoring for analytical hypotheses."""

from statistics import mean

from pydantic import BaseModel, Field

from backend.ai_intelligence.context.context_schema import (
    AnalyticalContext,
)
from backend.ai_intelligence.reasoning.reasoning_schema import (
    RootCauseHypothesis,
)

CONFIDENCE_VERSION = "1.0.0"

CONFIDENCE_WEIGHTS = {
    "dataCoverage": 25,
    "sampleAdequacy": 20,
    "supportingEvidence": 25,
    "counterEvidence": 15,
    "historicalConsistency": 15,
}

TARGET_SAMPLE_SIZE = 30
OBSERVATIONAL_CAP = 70
ESTIMATED_SOURCE_CAP = 60


class HypothesisConfidence(BaseModel):
    confidenceVersion: str = CONFIDENCE_VERSION

    confidenceScore: float = Field(ge=0, le=100)

    dimensions: dict[str, float]

    appliedCap: float

    limitations: list[str]


def coverage_score(
    percentage: float | None,
    status: str | None,
) -> float:
    """Use measured coverage or a conservative status fallback."""

    if percentage is not None:
        return max(0.0, min(100.0, percentage))

    return {
        "COMPLETE": 100.0,
        "ESTIMATED": 60.0,
        "PARTIAL": 40.0,
    }.get(status, 0.0)


def calculate_confidence(
    hypothesis: RootCauseHypothesis,
    facts: list[AnalyticalContext],
    source_coverage: str,
) -> HypothesisConfidence | None:
    """Estimate evidence strength, not causal probability."""

    fact_index = {fact.evidenceRef: fact for fact in facts}

    references = hypothesis.supportingEvidence

    all_references = references + hypothesis.counterEvidence

    if not references:
        return None

    for reference in all_references:
        fact = fact_index.get(reference.evidenceRef)

        if fact is None:
            return None

        if fact.direction != reference.direction:
            return None

    supporting = [fact_index[reference.evidenceRef] for reference in references]

    limitations = [
        "Observational evidence does not establish causation.",
        "Related metrics may represent overlapping observations.",
        "Confidence is a heuristic, not a calibrated probability.",
    ]

    # 01. Coverage across both comparison periods.

    data_coverage = mean(
        min(
            coverage_score(
                fact.enrichmentCoveragePct,
                fact.coverageStatus,
            ),
            coverage_score(
                fact.previousEnrichmentCoveragePct,
                fact.previousCoverageStatus,
            ),
        )
        for fact in supporting
    )

    # 02. Sample adequacy across both periods.

    sample_adequacy = mean(
        min(
            100.0,
            min(
                fact.sampleSize or 0,
                fact.previousSampleSize or 0,
            )
            / TARGET_SAMPLE_SIZE
            * 100,
        )
        for fact in supporting
    )

    # 03. Conservative supporting-evidence breadth.
    # Additional metrics are not independent causal evidence.

    evidence_strength = 60.0 if len({fact.metricId for fact in supporting}) >= 2 else 50.0

    # 04. Counter-evidence acknowledgement.

    counter_evidence = 60.0 if hypothesis.counterEvidence else 25.0

    if not hypothesis.counterEvidence:
        limitations.append("No explicit counter-evidence was cited.")

    # 05. Alignment with available historical benchmarks.

    historical_scores = []

    for fact in supporting:
        benchmark_change = fact.changeVsBenchmarkPct

        if benchmark_change is None or (fact.benchmarkPeriodCount or 0) < 2:
            continue

        benchmark_direction = (
            "INCREASED"
            if benchmark_change > 0
            else "DECREASED"
            if benchmark_change < 0
            else "UNCHANGED"
        )

        historical_scores.append(100.0 if benchmark_direction == fact.direction else 0.0)

    historical_consistency = mean(historical_scores) if historical_scores else 50.0

    if len(historical_scores) < len(supporting):
        limitations.append("Historical benchmark coverage is incomplete.")

    if not historical_scores:
        limitations.append(
            "A neutral historical score was used because no eligible benchmark was available."
        )

    dimensions = {
        "dataCoverage": round(data_coverage, 2),
        "sampleAdequacy": round(sample_adequacy, 2),
        "supportingEvidence": evidence_strength,
        "counterEvidence": counter_evidence,
        "historicalConsistency": round(historical_consistency, 2),
    }

    weighted_score = sum(
        dimensions[key] * weight / 100 for key, weight in CONFIDENCE_WEIGHTS.items()
    )

    cap = OBSERVATIONAL_CAP

    if source_coverage != "COMPLETE":
        cap = ESTIMATED_SOURCE_CAP

        limitations.append("Source coverage is not confirmed complete.")

    return HypothesisConfidence(
        confidenceScore=round(min(weighted_score, cap), 2),
        dimensions=dimensions,
        appliedCap=cap,
        limitations=limitations,
    )
