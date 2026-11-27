import pytest
from pydantic import ValidationError

from backend.ai_intelligence.context.context_schema import (
    AnalyticalContext,
    IntelligenceContext,
    SemanticContext,
)
from backend.ai_intelligence.reasoning.report_policy import (
    build_report_schema,
    observation_only_required,
)


def make_context(enriched=False):
    return IntelligenceContext.model_construct(
        semanticContext=[
            SemanticContext.model_construct(
                metricId="medianMergeHours",
                metricVersion="1.0.0",
                requiresDetailEnrichment=False,
                requiresReviewEnrichment=False,
            ),
            SemanticContext.model_construct(
                metricId="medianFirstReviewHours",
                metricVersion="1.0.0",
                requiresDetailEnrichment=False,
                requiresReviewEnrichment=True,
            ),
        ],
        analyticalContext=[
            AnalyticalContext(
                evidenceRef="E05",
                evidenceId="merge-duration",
                metricId="medianMergeHours",
                metricVersion="1.0.0",
                currentValue=100,
                previousValue=50,
                changeValue=50,
                changePct=100,
                direction="INCREASED",
                coverageStatus="ESTIMATED",
            ),
            AnalyticalContext(
                evidenceRef="E07",
                evidenceId="review-duration",
                metricId="medianFirstReviewHours",
                metricVersion="1.0.0",
                currentValue=20,
                previousValue=10 if enriched else None,
                changeValue=10 if enriched else None,
                changePct=100 if enriched else None,
                direction=("INCREASED" if enriched else "UNAVAILABLE"),
                coverageStatus="ESTIMATED",
            ),
        ],
    )


def test_missing_enrichment_requires_observation_only():
    assert observation_only_required(make_context())


def test_comparable_enrichment_permits_hypothesis():
    assert not observation_only_required(make_context(True))


def test_observation_only_report_accepted():
    schema = build_report_schema(make_context())

    output = schema.model_validate(
        {
            "status": "ANSWERED",
            "observationRefs": ["E05:+"],
            "hypothesis": None,
            "hypothesisRefs": [],
            "counterRefs": [],
            "alternative": None,
            "investigation": None,
        }
    )

    assert output.hypothesis is None


def test_unsupported_hypothesis_rejected():
    schema = build_report_schema(make_context())

    with pytest.raises(ValidationError):
        schema.model_validate(
            {
                "status": "ANSWERED",
                "observationRefs": ["E05:+"],
                "hypothesis": "Reviews may be taking longer.",
                "hypothesisRefs": ["E05:+"],
                "counterRefs": [],
                "alternative": None,
                "investigation": None,
            }
        )
