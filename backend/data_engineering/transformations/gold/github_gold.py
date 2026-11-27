"""Silver-to-Gold analytical transformation.

Engineering Intelligence Platform (EIP)
Layer: Gold
Component: Engineering Analytics

Responsibilities:
    - Calculate PR-level lifecycle facts.
    - Qualify external pull request reviews.
    - Calculate deterministic period metrics.
    - Generate historical comparisons and evidence identifiers.
    - Suppress metrics when required coverage is unavailable.
    - Persist Gold facts transactionally.

All metrics are calculated independently of the LLM.
"""

# ---------------------------------------------------------------------
# 01. Dependencies
# ---------------------------------------------------------------------

import json
from collections import defaultdict
from datetime import date, timedelta
from math import ceil, floor
from statistics import mean, median, stdev
from uuid import NAMESPACE_URL, uuid5

from dotenv import dotenv_values

from backend.data_engineering.database.connection import (
    initialize_database,
    open_database,
)
from backend.data_engineering.transformations.silver.github_silver import (
    RUN_TABLE,
    SILVER_PRS,
    SILVER_REPOSITORIES,
    SILVER_REVIEWS,
    write_rows,
)
from backend.pipelines.github_ingestion import (
    parse_timestamp,
    utc_timestamp,
)

# ---------------------------------------------------------------------
# 02. Database objects and analytical constants
# ---------------------------------------------------------------------

GOLD_LIFECYCLE = "eip_tbl_gold_prLifecycle_wide"
GOLD_FACTS = "eip_tbl_gold_periodFacts_long"

QUALIFYING_REVIEW_STATES = {
    "APPROVED",
    "CHANGES_REQUESTED",
    "COMMENTED",
    "DISMISSED",
}


# ---------------------------------------------------------------------
# 03. Statistical utilities
# ---------------------------------------------------------------------


def elapsed_hours(start: str, end: str) -> float:
    """Calculate elapsed calendar hours between valid timestamps."""

    return (parse_timestamp(end) - parse_timestamp(start)).total_seconds() / 3600


def safe_median(values: list) -> float | None:
    """Return NULL for an empty statistical population."""

    return median(values) if values else None


def safe_mean(values: list) -> float | None:
    """Return the arithmetic mean when observations exist."""

    return mean(values) if values else None


def percentile(values: list, probability: float) -> float | None:
    """Calculate percentile using linear interpolation."""

    if not values:
        return None

    ordered = sorted(values)
    position = (len(ordered) - 1) * probability

    lower = floor(position)
    upper = ceil(position)

    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def percentage(numerator, denominator) -> float | None:
    """Calculate a percentage with safe denominator handling."""

    if numerator is None or denominator in (None, 0):
        return None

    return 100 * numerator / denominator


def difference(current, previous) -> float | None:
    """Calculate absolute change between comparable values."""

    if current is None or previous is None:
        return None

    return current - previous


def percentage_change(current, previous) -> float | None:
    """Calculate relative change from a comparison value."""

    return percentage(
        difference(current, previous),
        previous,
    )


# ---------------------------------------------------------------------
# 04. PR lifecycle calculations
# ---------------------------------------------------------------------


def qualify_review(pr, review) -> bool:
    """Identify a submitted external review within the PR lifecycle."""

    return (
        pr["authorId"] is not None
        and review["reviewerId"] is not None
        and review["reviewerId"] != pr["authorId"]
        and review["reviewerType"] == "User"
        and review["reviewState"] in QUALIFYING_REVIEW_STATES
        and review["submittedAt"] is not None
        and pr["mergedAt"] is not None
        and pr["createdAt"] <= review["submittedAt"] <= pr["mergedAt"]
    )


def build_lifecycle(pr, reviews: list, calculated_at: str) -> dict:
    """Create one analytical lifecycle record."""

    merge_hours = None
    pre_review_hours = None
    post_review_hours = None

    first_review = None
    last_review = None
    review_count = None
    reviewer_ids = None

    if pr["mergedAt"] is not None:
        merge_hours = elapsed_hours(
            pr["createdAt"],
            pr["mergedAt"],
        )

    # Review statistics are available only for completed extraction.
    if pr["isMerged"] and pr["isReviewExtractionComplete"]:
        qualified = [review for review in reviews if qualify_review(pr, review)]

        review_count = len(qualified)

        reviewer_ids = sorted({review["reviewerId"] for review in qualified})

        if qualified:
            review_times = [review["submittedAt"] for review in qualified]

            first_review = min(review_times)
            last_review = max(review_times)

            pre_review_hours = elapsed_hours(
                pr["createdAt"],
                first_review,
            )

            post_review_hours = elapsed_hours(
                first_review,
                pr["mergedAt"],
            )

    lines_changed = None
    files_changed = None

    if pr["isDetailExtractionComplete"]:
        lines_changed = pr["additionsCount"] + pr["deletionsCount"]
        files_changed = pr["changedFilesCount"]

    return {
        "repositoryId": pr["repositoryId"],
        "pullRequestId": pr["pullRequestId"],
        "pullRequestNumber": pr["pullRequestNumber"],
        "authorId": pr["authorId"],
        "pullRequestState": pr["pullRequestState"],
        "isDraft": pr["isDraft"],
        "isMerged": pr["isMerged"],
        "createdAt": pr["createdAt"],
        "closedAt": pr["closedAt"],
        "mergedAt": pr["mergedAt"],
        "firstReviewAt": first_review,
        "lastReviewAt": last_review,
        "externalReviewCount": review_count,
        "uniqueExternalReviewerCount": (len(reviewer_ids) if reviewer_ids is not None else None),
        "externalReviewerIdsJson": (json.dumps(reviewer_ids) if reviewer_ids is not None else None),
        "linesChanged": lines_changed,
        "changedFilesCount": files_changed,
        "mergeHours": merge_hours,
        "preReviewHours": pre_review_hours,
        "postReviewHours": post_review_hours,
        "preReviewTimeSharePct": percentage(
            pre_review_hours,
            merge_hours,
        ),
        "isDetailExtractionComplete": pr["isDetailExtractionComplete"],
        "isReviewExtractionComplete": pr["isReviewExtractionComplete"],
        "ingestionRunId": pr["ingestionRunId"],
        "calculatedAt": calculated_at,
    }


# ---------------------------------------------------------------------
# 05. Period metric calculations
# ---------------------------------------------------------------------


def in_period(timestamp, start: date, end: date) -> bool:
    """Evaluate inclusive-start, exclusive-end UTC period membership."""

    return timestamp is not None and start.isoformat() <= timestamp[:10] < end.isoformat()


def metric_result(
    value,
    eligible_count,
    sample_size,
    enriched_count=None,
    status="ESTIMATED",
) -> dict:
    """Attach coverage metadata to a calculated metric."""

    if value is None and status == "ESTIMATED":
        status = "NO_SAMPLE"

    return {
        "value": value,
        "eligiblePRCount": eligible_count,
        "enrichedPRCount": enriched_count,
        "sampleSize": sample_size,
        "enrichmentCoveragePct": (
            percentage(enriched_count, eligible_count) if enriched_count is not None else None
        ),
        "coverageStatus": status,
    }


def calculate_period(
    lifecycle: list,
    run,
    metrics: list,
    start: date,
    end: date,
) -> dict:
    """Calculate all registered metrics for one reporting period."""

    if start >= end:
        raise ValueError("Reporting period must have a positive length.")

    history_start = date.fromisoformat(run["coverageStartAt"][:10])
    history_end = date.fromisoformat(run["coverageEndAt"][:10])
    enrichment_start = date.fromisoformat(run["enrichmentStartAt"][:10])

    # Do not present unavailable history as zero activity.
    if start < history_start or end > history_end or run["coverageStatus"] != "ESTIMATED":
        return {
            metric["metricId"]: metric_result(
                None,
                None,
                None,
                status="INSUFFICIENT_SOURCE_COVERAGE",
            )
            for metric in metrics
        }

    opened = [pr for pr in lifecycle if in_period(pr["createdAt"], start, end)]

    merged = [pr for pr in lifecycle if in_period(pr["mergedAt"], start, end)]

    closed = [pr for pr in lifecycle if in_period(pr["closedAt"], start, end)]

    closed_without_merge = [pr for pr in closed if not pr["isMerged"]]

    merged_count = len(merged)

    merge_durations = [pr["mergeHours"] for pr in merged if pr["mergeHours"] is not None]

    # 05.01. Basic lifecycle metrics.

    results = {
        "prsOpened": metric_result(len(opened), len(opened), len(opened)),
        "prsMerged": metric_result(merged_count, merged_count, merged_count),
        "prsClosed": metric_result(len(closed), len(closed), len(closed)),
        "prsClosedWithoutMerge": metric_result(
            len(closed_without_merge),
            len(closed),
            len(closed_without_merge),
        ),
        "medianMergeHours": metric_result(
            safe_median(merge_durations),
            merged_count,
            len(merge_durations),
        ),
        "p90MergeHours": metric_result(
            percentile(merge_durations, 0.90),
            merged_count,
            len(merge_durations),
        ),
    }

    # 05.02. Determine review and detail extraction coverage.

    review_enriched = [pr for pr in merged if pr["isReviewExtractionComplete"]]

    detail_enriched = [pr for pr in merged if pr["isDetailExtractionComplete"]]

    reviewed = [pr for pr in review_enriched if pr["firstReviewAt"] is not None]

    def enriched_result(value, sample_size, enriched):
        """Publish full-cohort metrics only with complete enrichment."""

        enriched_count = len(enriched)

        if start < enrichment_start:
            return metric_result(
                None,
                merged_count,
                None,
                enriched_count,
                status="OUTSIDE_ENRICHMENT_WINDOW",
            )

        if enriched_count != merged_count:
            return metric_result(
                None,
                merged_count,
                None,
                enriched_count,
                status="INCOMPLETE_ENRICHMENT",
            )

        return metric_result(
            value,
            merged_count,
            sample_size,
            enriched_count,
        )

    # 05.03. Collaboration metrics.

    pre_review = [pr["preReviewHours"] for pr in reviewed]
    post_review = [pr["postReviewHours"] for pr in reviewed]

    reviewed_merge_hours = [pr["mergeHours"] for pr in reviewed]

    distinct_reviewers = {
        reviewer_id
        for pr in review_enriched
        for reviewer_id in json.loads(pr["externalReviewerIdsJson"] or "[]")
    }

    review_values = {
        "medianFirstReviewHours": (safe_median(pre_review), len(reviewed)),
        "meanPreReviewHours": (safe_mean(pre_review), len(reviewed)),
        "meanPostReviewHours": (safe_mean(post_review), len(reviewed)),
        "preReviewTimeSharePct": (
            percentage(
                sum(pre_review),
                sum(reviewed_merge_hours),
            ),
            len(reviewed),
        ),
        "mergedPRReviewCoveragePct": (
            percentage(len(reviewed), merged_count),
            merged_count,
        ),
        "uniqueExternalReviewers": (len(distinct_reviewers), merged_count),
    }

    for metric_id, (value, sample_size) in review_values.items():
        results[metric_id] = enriched_result(value, sample_size, review_enriched)

    # 05.04. Code change metrics.

    for metric_id, column in (
        ("medianLinesChanged", "linesChanged"),
        ("medianFilesChanged", "changedFilesCount"),
    ):
        values = [pr[column] for pr in detail_enriched if pr[column] is not None]

        results[metric_id] = enriched_result(
            safe_median(values),
            len(values),
            detail_enriched,
        )

    if set(results) != {metric["metricId"] for metric in metrics}:
        raise RuntimeError("Metric registry reconciliation failed.")

    return results


# ---------------------------------------------------------------------
# 06. Comparative facts and evidence identifiers
# ---------------------------------------------------------------------


def build_period_facts(
    lifecycle: list,
    run,
    metrics: list,
    start: date,
    end: date,
    benchmark_count: int,
    calculated_at: str,
    cache: dict,
) -> list[dict]:
    """Build comparable period facts for the API and AI engine."""

    period_length = end - start

    def get_period(period_end):
        period_start = period_end - period_length
        key = (period_start, period_end)

        if key not in cache:
            cache[key] = calculate_period(
                lifecycle,
                run,
                metrics,
                period_start,
                period_end,
            )

        return cache[key]

    current = get_period(end)
    previous = get_period(start)

    historical = [
        get_period(end - period_length * offset) for offset in range(1, benchmark_count + 1)
    ]

    facts = []

    for metric in metrics:
        metric_id = metric["metricId"]

        current_result = current[metric_id]
        previous_result = previous[metric_id]

        current_value = current_result["value"]
        previous_value = previous_result["value"]

        historical_values = []

        if metric["supportsHistoricalBenchmark"]:
            historical_values = [
                period[metric_id]["value"]
                for period in historical
                if period[metric_id]["value"] is not None
            ]

        # Require every configured benchmark period.
        benchmark_complete = len(historical_values) == benchmark_count and benchmark_count > 0

        benchmark_avg = mean(historical_values) if benchmark_complete else None

        benchmark_std = (
            stdev(historical_values) if benchmark_complete and benchmark_count > 1 else None
        )

        # Evidence IDs are deterministic within the source snapshot.
        evidence_key = (
            f"{run['ingestionRunId']}:{run['repositoryId']}:"
            f"{start}:{end}:{metric_id}:{metric['metricVersion']}"
        )

        facts.append(
            {
                "repositoryId": run["repositoryId"],
                "periodType": "ROLLING",
                "periodStart": start.isoformat(),
                "periodEndExclusive": end.isoformat(),
                "metricId": metric_id,
                "metricVersion": metric["metricVersion"],
                "metricUnit": metric["metricUnit"],
                "currentValue": current_value,
                "previousValue": previous_value,
                "changeValue": difference(current_value, previous_value),
                "changePct": percentage_change(current_value, previous_value),
                "historicalBenchmarkAvg": benchmark_avg,
                "historicalBenchmarkStd": benchmark_std,
                "changeVsBenchmarkPct": percentage_change(current_value, benchmark_avg),
                "benchmarkPeriodCount": len(historical_values),
                "eligiblePRCount": current_result["eligiblePRCount"],
                "enrichedPRCount": current_result["enrichedPRCount"],
                "sampleSize": current_result["sampleSize"],
                "enrichmentCoveragePct": (current_result["enrichmentCoveragePct"]),
                "coverageStatus": current_result["coverageStatus"],
                "previousSampleSize": previous_result["sampleSize"],
                "previousEnrichmentCoveragePct": (previous_result["enrichmentCoveragePct"]),
                "previousCoverageStatus": (previous_result["coverageStatus"]),
                "evidenceId": str(uuid5(NAMESPACE_URL, evidence_key)),
                "ingestionRunId": run["ingestionRunId"],
                "calculatedAt": calculated_at,
            }
        )

    return facts


# ---------------------------------------------------------------------
# 07. Gold transformation orchestration
# ---------------------------------------------------------------------


def refresh_gold(database_path: str, repository: str) -> dict:
    """Refresh Gold from the currently published Silver snapshot."""

    initialize_database(database_path)

    calculated_at = utc_timestamp()

    with open_database(database_path) as connection:
        connection.execute("BEGIN IMMEDIATE")

        # 07.01. Resolve the Silver snapshot and source run.

        repo = connection.execute(
            f"""
            SELECT *
            FROM {SILVER_REPOSITORIES}
            WHERE repositoryFullName = ? COLLATE NOCASE
            """,
            (repository,),
        ).fetchone()

        if repo is None:
            raise RuntimeError("Silver repository snapshot not found.")

        repository_id = repo["repositoryId"]
        run_id = repo["ingestionRunId"]

        run = connection.execute(
            f"""
            SELECT *
            FROM {RUN_TABLE}
            WHERE ingestionRunId = ?
              AND runStatus = 'SUCCEEDED'
            """,
            (run_id,),
        ).fetchone()

        if run is None:
            raise RuntimeError("Successful source execution not found.")

        config = dict(
            connection.execute("""
            SELECT configKey, configValue
            FROM eip_vw_control_pipelineConfig_static
            WHERE isActive = 1
        """).fetchall()
        )

        metrics = connection.execute("""
            SELECT *
            FROM eip_vw_control_metricRegistry_static
            WHERE isActive = 1
            ORDER BY displaySequence
        """).fetchall()

        # 07.02. Read standardized Silver data.

        prs = connection.execute(
            f"""
            SELECT *
            FROM {SILVER_PRS}
            WHERE repositoryId = ?
            """,
            (repository_id,),
        ).fetchall()

        reviews = connection.execute(
            f"""
            SELECT *
            FROM {SILVER_REVIEWS}
            WHERE repositoryId = ?
            """,
            (repository_id,),
        ).fetchall()

        if any(row["ingestionRunId"] != run_id for row in (*prs, *reviews)):
            raise RuntimeError("Mixed Silver source snapshots detected.")

        # Index reviews by PR to avoid repeated full-table scans.

        reviews_by_pr = defaultdict(list)

        for review in reviews:
            reviews_by_pr[review["pullRequestId"]].append(review)

        # 07.03. Calculate lifecycle facts.

        lifecycle = [
            build_lifecycle(
                pr,
                reviews_by_pr.get(pr["pullRequestId"], []),
                calculated_at,
            )
            for pr in prs
        ]

        # Reconcile the pre-review and post-review durations.

        for pr in lifecycle:
            if pr["firstReviewAt"] is not None:
                reconstructed = pr["preReviewHours"] + pr["postReviewHours"]

                if abs(reconstructed - pr["mergeHours"]) > 0.000001:
                    raise RuntimeError("Lifecycle duration reconciliation failed.")

        # 07.04. Materialize current and historical period facts.

        reporting_end = date.fromisoformat(run["coverageEndAt"][:10])

        period_length = timedelta(days=int(config["reportingPeriodDays"]))

        benchmark_count = int(config["benchmarkPeriodCount"])

        facts = []
        period_cache = {}

        # Default current period plus preceding benchmark periods.
        # Older enrichment metrics remain NULL when unavailable.

        for offset in range(benchmark_count + 1):
            end = reporting_end - period_length * offset
            start = end - period_length

            facts.extend(
                build_period_facts(
                    lifecycle,
                    run,
                    metrics,
                    start,
                    end,
                    benchmark_count,
                    calculated_at,
                    period_cache,
                )
            )

        # 07.05. Replace Gold data atomically.

        for table in (GOLD_FACTS, GOLD_LIFECYCLE):
            connection.execute(
                f"DELETE FROM {table} WHERE repositoryId = ?",
                (repository_id,),
            )

        lifecycle_count = write_rows(connection, GOLD_LIFECYCLE, lifecycle)

        fact_count = write_rows(connection, GOLD_FACTS, facts)

        if lifecycle_count != len(prs):
            raise RuntimeError("Gold lifecycle reconciliation failed.")

        if fact_count != len(metrics) * (benchmark_count + 1):
            raise RuntimeError("Gold metric inventory reconciliation failed.")

        if connection.execute("PRAGMA foreign_key_check").fetchall():
            raise RuntimeError("Gold foreign key validation failed.")

        summary = {
            "Source Run": run_id,
            "Gold Lifecycle Records": lifecycle_count,
            "Registered Metrics": len(metrics),
            "Materialized Reporting Periods": benchmark_count + 1,
            "Gold Period Facts": fact_count,
            "Current Period Start": str(reporting_end - period_length),
            "Current Period End Exclusive": str(reporting_end),
            "Source Coverage": run["coverageStatus"],
        }

    # Report success only after the transaction commits.

    print("=" * 70)
    print("EIP | Gold Transformation Summary")
    print("=" * 70)

    for name, value in summary.items():
        print(f"{name:<32}: {value}")

    print("Transformation Status: SUCCEEDED")
    print("=" * 70)

    return summary


# ---------------------------------------------------------------------
# 08. Command-line entry point
# ---------------------------------------------------------------------

if __name__ == "__main__":
    environment = dotenv_values(".env")

    database_path = environment.get("DATABASE_PATH") or "data/eip.db"

    repository = environment.get("GITHUB_REPOSITORY")

    if not repository:
        raise RuntimeError("GitHub repository configuration is missing.")

    refresh_gold(database_path, repository)
