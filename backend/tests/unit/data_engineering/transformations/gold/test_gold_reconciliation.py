"""Independent reconciliation of PR lifecycle and period metrics."""

from datetime import date

import pytest

from backend.data_engineering.transformations.gold.github_gold import (
    build_lifecycle,
    build_period_facts,
    calculate_period,
)

START = date(2026, 11, 20)
END = date(2026, 11, 27)

CALCULATED_AT = "2026-11-27T00:00:00Z"

METRIC_IDS = [
    "prsOpened",
    "prsMerged",
    "prsClosed",
    "prsClosedWithoutMerge",
    "medianMergeHours",
    "p90MergeHours",
    "medianFirstReviewHours",
    "meanPreReviewHours",
    "meanPostReviewHours",
    "preReviewTimeSharePct",
    "mergedPRReviewCoveragePct",
    "uniqueExternalReviewers",
    "medianLinesChanged",
    "medianFilesChanged",
]


def make_pr(
    number,
    created,
    merged=None,
    closed=None,
    lines=0,
    files=0,
    **overrides,
):
    values = {
        "repositoryId": 123,
        "pullRequestId": number,
        "pullRequestNumber": number,
        "authorId": 1,
        "pullRequestState": ("closed" if merged or closed else "open"),
        "isDraft": False,
        "isMerged": merged is not None,
        "createdAt": created,
        "mergedAt": merged,
        "closedAt": closed or merged,
        "isReviewExtractionComplete": True,
        "isDetailExtractionComplete": True,
        "additionsCount": lines,
        "deletionsCount": 0,
        "changedFilesCount": files,
        "ingestionRunId": "test-run",
    }

    values.update(overrides)
    return values


def make_review(timestamp, reviewer=2, **overrides):
    values = {
        "reviewerId": reviewer,
        "reviewerType": "User",
        "reviewState": "APPROVED",
        "submittedAt": timestamp,
    }

    values.update(overrides)
    return values


@pytest.fixture
def dataset():

    pr_a = make_pr(
        1,
        "2026-11-19T00:00:00Z",
        "2026-11-21T00:00:00Z",
        lines=30,
        files=3,
    )

    pr_b = make_pr(
        2,
        "2026-11-20T00:00:00Z",
        "2026-11-20T12:00:00Z",
        lines=10,
        files=1,
    )

    pr_c = make_pr(
        3,
        "2026-11-26T00:00:00Z",
        "2026-11-26T06:00:00Z",
    )

    pr_d = make_pr(
        4,
        "2026-11-22T00:00:00Z",
        closed="2026-11-23T00:00:00Z",
    )

    pr_e = make_pr(
        5,
        "2026-11-26T00:00:00Z",
    )

    pr_f = make_pr(
        6,
        "2026-11-14T00:00:00Z",
        "2026-11-15T00:00:00Z",
    )

    source = [
        (
            pr_a,
            [
                make_review("2026-11-20T00:00:00Z"),
                make_review(
                    "2026-11-20T02:00:00Z",
                    reviewer=3,
                ),
                make_review("2026-11-20T04:00:00Z"),
            ],
        ),
        (
            pr_b,
            [make_review("2026-11-20T02:00:00Z")],
        ),
        (pr_c, []),
        (pr_d, []),
        (pr_e, []),
        (
            pr_f,
            [make_review("2026-11-14T04:00:00Z")],
        ),
    ]

    lifecycle = [build_lifecycle(pr, reviews, CALCULATED_AT) for pr, reviews in source]

    run = {
        "repositoryId": 123,
        "ingestionRunId": "test-run",
        "coverageStartAt": "2026-11-01T00:00:00Z",
        "coverageEndAt": "2026-11-27T00:00:00Z",
        "enrichmentStartAt": "2026-11-13T00:00:00Z",
        "coverageStatus": "ESTIMATED",
    }

    metrics = [
        {
            "metricId": metric_id,
            "metricVersion": "1.0.0",
            "metricUnit": "TEST_UNIT",
            "supportsHistoricalBenchmark": index < 6,
        }
        for index, metric_id in enumerate(METRIC_IDS)
    ]

    return lifecycle, run, metrics


def test_all_fourteen_metrics(dataset):
    lifecycle, run, metrics = dataset

    results = calculate_period(lifecycle, run, metrics, START, END)

    expected = {
        "prsOpened": 4,
        "prsMerged": 3,
        "prsClosed": 4,
        "prsClosedWithoutMerge": 1,
        "medianMergeHours": 12,
        "p90MergeHours": 40.8,
        "medianFirstReviewHours": 13,
        "meanPreReviewHours": 13,
        "meanPostReviewHours": 17,
        "preReviewTimeSharePct": 100 * 26 / 60,
        "mergedPRReviewCoveragePct": 100 * 2 / 3,
        "uniqueExternalReviewers": 2,
        "medianLinesChanged": 10,
        "medianFilesChanged": 1,
    }

    assert set(results) == set(expected)

    for metric_id, value in expected.items():
        assert results[metric_id]["value"] == pytest.approx(value), metric_id

    assert results["medianFirstReviewHours"]["sampleSize"] == 2
    assert results["medianMergeHours"]["sampleSize"] == 3
    assert results["medianFirstReviewHours"]["eligiblePRCount"] == 3
    assert results["medianFirstReviewHours"]["enrichmentCoveragePct"] == 100


def test_review_qualification():
    pr = make_pr(
        1,
        "2026-11-20T00:00:00Z",
        "2026-11-21T00:00:00Z",
    )

    reviews = [
        # Valid external reviews.
        make_review("2026-11-20T06:00:00Z"),
        make_review("2026-11-20T12:00:00Z"),
        # Self-review.
        make_review(
            "2026-11-20T01:00:00Z",
            reviewer=1,
        ),
        # Bot review.
        make_review(
            "2026-11-20T02:00:00Z",
            reviewer=3,
            reviewerType="Bot",
        ),
        # Before creation.
        make_review("2026-11-19T12:00:00Z"),
        # After merge.
        make_review("2026-11-22T00:00:00Z"),
        # Unsubmitted review.
        make_review(None, reviewState="PENDING"),
    ]

    result = build_lifecycle(pr, reviews, CALCULATED_AT)

    assert result["externalReviewCount"] == 2
    assert result["uniqueExternalReviewerCount"] == 1
    assert result["mergeHours"] == 24
    assert result["preReviewHours"] == 6
    assert result["postReviewHours"] == 18
    assert result["preReviewTimeSharePct"] == 25


def test_unreviewed_pr_is_not_zero_duration(dataset):
    lifecycle, _, _ = dataset

    result = lifecycle[2]

    assert result["mergeHours"] == 6
    assert result["externalReviewCount"] == 0
    assert result["preReviewHours"] is None
    assert result["postReviewHours"] is None


def test_incomplete_review_enrichment(dataset):
    lifecycle, run, metrics = dataset

    lifecycle[0]["isReviewExtractionComplete"] = False

    results = calculate_period(lifecycle, run, metrics, START, END)

    review = results["medianFirstReviewHours"]

    assert review["value"] is None
    assert review["coverageStatus"] == "INCOMPLETE_ENRICHMENT"
    assert review["enrichmentCoveragePct"] == pytest.approx(100 * 2 / 3)

    # Basic and independently enriched metrics remain valid.
    assert results["prsMerged"]["value"] == 3
    assert results["medianLinesChanged"]["value"] == 10


def test_outside_enrichment_window(dataset):
    lifecycle, run, metrics = dataset

    run["enrichmentStartAt"] = "2026-11-21T00:00:00Z"

    results = calculate_period(lifecycle, run, metrics, START, END)

    assert results["prsMerged"]["value"] == 3
    assert results["medianFirstReviewHours"]["value"] is None
    assert results["medianFirstReviewHours"]["coverageStatus"] == "OUTSIDE_ENRICHMENT_WINDOW"


def test_unavailable_history_is_not_zero(dataset):
    lifecycle, run, metrics = dataset

    results = calculate_period(
        lifecycle,
        run,
        metrics,
        date(2026, 10, 1),
        date(2026, 10, 8),
    )

    assert all(result["value"] is None for result in results.values())

    assert all(
        result["coverageStatus"] == "INSUFFICIENT_SOURCE_COVERAGE" for result in results.values()
    )


def test_invalid_reporting_period(dataset):
    lifecycle, run, metrics = dataset

    with pytest.raises(ValueError):
        calculate_period(lifecycle, run, metrics, END, START)


def make_facts(dataset):
    lifecycle, run, metrics = dataset

    return {
        fact["metricId"]: fact
        for fact in build_period_facts(
            lifecycle,
            run,
            metrics,
            START,
            END,
            2,
            CALCULATED_AT,
            {},
        )
    }


def test_comparative_facts_and_benchmarks(dataset):
    facts = make_facts(dataset)

    merged = facts["prsMerged"]

    assert merged["currentValue"] == 3
    assert merged["previousValue"] == 1
    assert merged["changeValue"] == 2
    assert merged["changePct"] == 200

    # Previous two periods contain one and zero merged PRs.
    assert merged["historicalBenchmarkAvg"] == 0.5
    assert merged["historicalBenchmarkStd"] == pytest.approx(0.70710678)
    assert merged["changeVsBenchmarkPct"] == 500
    assert merged["benchmarkPeriodCount"] == 2

    review = facts["medianFirstReviewHours"]

    assert review["currentValue"] == 13
    assert review["previousValue"] == 4
    assert review["changePct"] == 225
    assert review["historicalBenchmarkAvg"] is None


def test_partial_benchmark_is_withheld(dataset):
    _, run, _ = dataset

    run["coverageStartAt"] = "2026-11-13T00:00:00Z"

    merged = make_facts(dataset)["prsMerged"]

    assert merged["benchmarkPeriodCount"] == 1
    assert merged["historicalBenchmarkAvg"] is None
    assert merged["historicalBenchmarkStd"] is None
    assert merged["changeVsBenchmarkPct"] is None


def test_evidence_identifiers_are_deterministic(dataset):
    first = make_facts(dataset)
    second = make_facts(dataset)

    assert first == second

    identifiers = {fact["evidenceId"] for fact in first.values()}

    assert len(identifiers) == 14

    _, run, _ = dataset

    run["ingestionRunId"] = "another-run"

    refreshed = make_facts(dataset)

    assert first["prsMerged"]["evidenceId"] != refreshed["prsMerged"]["evidenceId"]
