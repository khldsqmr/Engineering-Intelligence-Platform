"""Deterministic tests for hypothesis evidence-strength scoring."""

import pytest

from backend.ai_intelligence.confidence.confidence import (
    calculate_confidence,
    coverage_score,
)
from backend.ai_intelligence.context.context_schema import (
    AnalyticalContext,
)
from backend.ai_intelligence.reasoning.reasoning_schema import (
    RootCauseHypothesis,
)


def make_fact(
    ref="E01",
    metric_id="medianFirstReviewHours",
    **overrides,
):
    values = {
        "evidenceRef": ref,
        "evidenceId": f"test-{ref}",
        "metricId": metric_id,
        "metricVersion": "1.0.0",
        "currentValue": 12.0,
        "previousValue": 8.0,
        "changeValue": 4.0,
        "changePct": 50.0,
        "direction": "INCREASED",
        "historicalBenchmarkAvg": None,
        "historicalBenchmarkStd": None,
        "changeVsBenchmarkPct": None,
        "benchmarkPeriodCount": 0,
        "eligiblePRCount": 100,
        "enrichedPRCount": 100,
        "sampleSize": 100,
        "enrichmentCoveragePct": 100.0,
        "coverageStatus": "COMPLETE",
        "previousSampleSize": 100,
        "previousEnrichmentCoveragePct": 100.0,
        "previousCoverageStatus": "COMPLETE",
    }

    values.update(overrides)

    return AnalyticalContext.model_validate(values)


def make_hypothesis(
    refs=("E01",),
    counter_refs=(),
):
    return RootCauseHypothesis.model_validate(
        {
            "text": "Longer initial review times may contribute to delays.",
            "supportingEvidence": [
                {
                    "evidenceRef": ref,
                    "direction": "INCREASED",
                }
                for ref in refs
            ],
            "counterEvidence": [
                {
                    "evidenceRef": ref,
                    "direction": "DECREASED",
                }
                for ref in counter_refs
            ],
        }
    )


@pytest.mark.parametrize(
    ("percentage", "status", "expected"),
    [
        (80.0, "COMPLETE", 80.0),
        (120.0, "COMPLETE", 100.0),
        (-5.0, "COMPLETE", 0.0),
        (None, "COMPLETE", 100.0),
        (None, "ESTIMATED", 60.0),
        (None, "PARTIAL", 40.0),
        (None, None, 0.0),
    ],
)
def test_coverage_score(percentage, status, expected):
    assert coverage_score(percentage, status) == expected


def test_single_supporting_metric():
    result = calculate_confidence(
        make_hypothesis(),
        [make_fact()],
        "COMPLETE",
    )

    assert result is not None
    assert result.confidenceScore == 68.75
    assert result.dimensions["supportingEvidence"] == 50
    assert result.dimensions["counterEvidence"] == 25
    assert result.dimensions["historicalConsistency"] == 50


@pytest.mark.parametrize(
    ("coverage", "expected_cap"),
    [
        ("COMPLETE", 70.0),
        ("ESTIMATED", 60.0),
        ("PARTIAL", 60.0),
    ],
)
def test_observational_confidence_caps(coverage, expected_cap):
    result = calculate_confidence(
        make_hypothesis(("E01", "E02")),
        [
            make_fact(),
            make_fact("E02", "meanPreReviewHours"),
        ],
        coverage,
    )

    assert result is not None
    assert result.confidenceScore == expected_cap
    assert result.appliedCap == expected_cap


def test_unknown_evidence_reference():
    result = calculate_confidence(
        make_hypothesis(("E99",)),
        [make_fact()],
        "COMPLETE",
    )

    assert result is None


def test_incorrect_evidence_direction():
    result = calculate_confidence(
        make_hypothesis(),
        [make_fact(direction="DECREASED")],
        "COMPLETE",
    )

    assert result is None


def test_previous_period_coverage_limits_confidence():
    result = calculate_confidence(
        make_hypothesis(),
        [
            make_fact(
                previousEnrichmentCoveragePct=40.0,
                previousSampleSize=3,
            )
        ],
        "COMPLETE",
    )

    assert result is not None
    assert result.dimensions["dataCoverage"] == 40.0
    assert result.dimensions["sampleAdequacy"] == 10.0
    assert result.confidenceScore == 35.75


def test_missing_sample_size():
    result = calculate_confidence(
        make_hypothesis(),
        [make_fact(previousSampleSize=None)],
        "COMPLETE",
    )

    assert result is not None
    assert result.dimensions["sampleAdequacy"] == 0


def test_counter_evidence_acknowledgement():
    result = calculate_confidence(
        make_hypothesis(
            ("E01",),
            counter_refs=("E02",),
        ),
        [
            make_fact(),
            make_fact(
                "E02",
                "meanPostReviewHours",
                currentValue=8.0,
                previousValue=12.0,
                changeValue=-4.0,
                changePct=-33.33,
                direction="DECREASED",
            ),
        ],
        "COMPLETE",
    )

    assert result is not None
    assert result.dimensions["counterEvidence"] == 60


@pytest.mark.parametrize(
    ("benchmark_change", "expected"),
    [
        (40.0, 100.0),
        (-40.0, 0.0),
    ],
)
def test_historical_direction_alignment(benchmark_change, expected):
    result = calculate_confidence(
        make_hypothesis(),
        [
            make_fact(
                changeVsBenchmarkPct=benchmark_change,
                benchmarkPeriodCount=4,
            )
        ],
        "COMPLETE",
    )

    assert result is not None
    assert result.dimensions["historicalConsistency"] == expected


def test_insufficient_historical_benchmarks():
    result = calculate_confidence(
        make_hypothesis(),
        [
            make_fact(
                changeVsBenchmarkPct=40.0,
                benchmarkPeriodCount=1,
            )
        ],
        "COMPLETE",
    )

    assert result is not None
    assert result.dimensions["historicalConsistency"] == 50
