"""Unit tests for deterministic context engineering."""

import pytest

from backend.ai_intelligence.context.context_builder import (
    build_context,
    determine_direction,
)


@pytest.fixture
def analytics():
    return {
        "repository": "example/repository",
        "repositoryId": 1,
        "ingestionRunId": "test-run",
        "periodStart": "2026-11-20",
        "periodEndExclusive": "2026-11-27",
        "previousPeriodStart": "2026-11-13",
        "previousPeriodEndExclusive": "2026-11-20",
        "reportingTimezone": "UTC",
        "sourceCoverage": "ESTIMATED",
        "dataRefreshedAt": "2026-11-27T00:00:00Z",
        "availableHistory": {
            "start": "2026-09-28T00:00:00Z",
            "endExclusive": "2026-11-27T00:00:00Z",
            "enrichmentStart": "2026-11-13T00:00:00Z",
        },
        "metrics": [
            {
                "metricId": "medianMergeHours",
                "metricVersion": "1.0.0",
                "metricName": "Median Merge Hours",
                "metricCategory": "LIFECYCLE",
                "metricDescription": "Median merge duration.",
                "metricUnit": "HOURS",
                "calculationDefinition": "Median merge hours.",
                "analyticalCohort": "MERGED_IN_PERIOD",
                "aggregationType": "MEDIAN",
                "periodEventAttribute": "mergedAt",
                "sourceDependencies": "SRC-002",
                "requiresDetailEnrichment": False,
                "requiresReviewEnrichment": False,
                "performanceDirection": "LOWER_IS_BETTER",
                "supportsHistoricalBenchmark": True,
                "interpretationGuidance": "Elapsed duration.",
                "evidenceId": "test-evidence",
                "currentValue": 90.0,
                "previousValue": 45.0,
                "changeValue": 45.0,
                "changePct": 100.0,
                "sampleSize": 100,
                "coverageStatus": "ESTIMATED",
            }
        ],
    }


@pytest.mark.parametrize(
    ("current", "previous", "expected"),
    [
        (20, 10, "INCREASED"),
        (10, 20, "DECREASED"),
        (10, 10, "UNCHANGED"),
        (0, 10, "DECREASED"),
        (10, 0, "INCREASED"),
        (0, 0, "UNCHANGED"),
        (None, 10, "UNAVAILABLE"),
        (10, None, "UNAVAILABLE"),
        (None, None, "UNAVAILABLE"),
    ],
)
def test_metric_direction(current, previous, expected):
    assert determine_direction(current, previous) == expected


def test_context_assembly(analytics):
    context = build_context(analytics)

    assert context.contextVersion == "1.0.0"
    assert context.repositoryId == 1
    assert len(context.semanticContext) == 1
    assert len(context.analyticalContext) == 1
    assert context.historicalContext == []

    evidence = context.analyticalContext[0]

    assert evidence.evidenceRef == "E01"
    assert evidence.evidenceId == "test-evidence"
    assert evidence.direction == "INCREASED"
    assert evidence.changePct == 100.0


def test_context_preserves_metric_semantics(analytics):
    context = build_context(analytics)
    metric = context.semanticContext[0]

    assert metric.aggregationType == "MEDIAN"
    assert metric.analyticalCohort == "MERGED_IN_PERIOD"
    assert metric.periodEventAttribute == "mergedAt"


def test_missing_values(analytics):
    analytics["metrics"][0]["currentValue"] = None
    analytics["metrics"][0]["changeValue"] = None
    analytics["metrics"][0]["changePct"] = None

    context = build_context(analytics)

    assert context.analyticalContext[0].direction == "UNAVAILABLE"
    assert any("unavailable" in item.lower() for item in context.qualityContext.limitations)


def test_duplicate_metric_rejected(analytics):
    analytics["metrics"].append(
        {
            **analytics["metrics"][0],
            "evidenceId": "another-evidence",
        }
    )

    with pytest.raises(ValueError, match="Duplicate metric"):
        build_context(analytics)


def test_duplicate_evidence_rejected(analytics):
    analytics["metrics"].append(
        {
            **analytics["metrics"][0],
            "metricId": "anotherMetric",
        }
    )

    with pytest.raises(ValueError, match="Duplicate evidence"):
        build_context(analytics)


def test_empty_metrics_rejected(analytics):
    analytics["metrics"] = []

    with pytest.raises(ValueError, match="No analytical metrics"):
        build_context(analytics)


def test_question_context(analytics):
    context = build_context(
        analytics,
        mode="question",
        question="  Why did merge duration increase?  ",
    )

    assert context.userIntent.mode == "question"
    assert context.userIntent.question == "Why did merge duration increase?"


def test_question_required(analytics):
    with pytest.raises(ValueError, match="requires a question"):
        build_context(analytics, mode="question")


def test_narrative_rejects_question(analytics):
    with pytest.raises(ValueError, match="does not accept"):
        build_context(
            analytics,
            mode="narrative",
            question="Unexpected question",
        )


def test_source_coverage_limitation(analytics):
    context = build_context(analytics)

    assert any(
        "not confirmed exhaustive" in item.lower() for item in context.qualityContext.limitations
    )


def test_context_is_serializable(analytics):
    context = build_context(analytics)

    restored = type(context).model_validate_json(context.model_dump_json())

    assert restored == context
