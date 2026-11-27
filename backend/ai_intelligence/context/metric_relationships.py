from backend.ai_intelligence.context.context_schema import (
    RelationalContext,
)

METRIC_RELATIONSHIPS = (
    RelationalContext(
        relationshipId="REL001",
        relationshipType="LIFECYCLE_DECOMPOSITION",
        metricIds=[
            "medianMergeHours",
            "meanPreReviewHours",
            "meanPostReviewHours",
            "preReviewTimeSharePct",
        ],
        interpretation=(
            "For an individual qualifying reviewed PR, "
            "merge duration equals pre-review duration "
            "plus post-review duration. "
            "The mean components must not be used to "
            "decompose the overall median merge duration."
        ),
    ),
    RelationalContext(
        relationshipId="REL002",
        relationshipType="REVIEW_ENGAGEMENT",
        metricIds=[
            "medianFirstReviewHours",
            "meanPreReviewHours",
            "mergedPRReviewCoveragePct",
            "uniqueExternalReviewers",
        ],
        interpretation=(
            "These metrics describe different aspects "
            "of initial review engagement and reviewer "
            "participation. They do not directly measure "
            "reviewer workload or availability."
        ),
    ),
    RelationalContext(
        relationshipId="REL003",
        relationshipType="CODE_CHANGE_SIZE",
        metricIds=[
            "medianLinesChanged",
            "medianFilesChanged",
            "medianMergeHours",
        ],
        interpretation=(
            "Lines changed and files changed are proxies "
            "for code change size. They are not direct "
            "measurements of technical complexity."
        ),
    ),
    RelationalContext(
        relationshipId="REL004",
        relationshipType="THROUGHPUT",
        metricIds=[
            "prsOpened",
            "prsMerged",
            "prsClosed",
            "prsClosedWithoutMerge",
        ],
        interpretation=(
            "These metrics describe PR activity and "
            "throughput. Opened and merged PRs belong "
            "to different event-based cohorts. "
            "They must not be interpreted as a direct "
            "conversion funnel or developer productivity."
        ),
    ),
    RelationalContext(
        relationshipId="REL005",
        relationshipType="DISTRIBUTION",
        metricIds=[
            "medianMergeHours",
            "p90MergeHours",
        ],
        interpretation=(
            "Median merge duration represents the "
            "central tendency. P90 represents the "
            "upper tail of the distribution. "
            "Changes may reflect a shift in PR cohort "
            "composition rather than process degradation."
        ),
    ),
)


def get_metric_relationships(
    metric_ids: set[str],
) -> list[RelationalContext]:

    return [
        relationship
        for relationship in METRIC_RELATIONSHIPS
        if set(relationship.metricIds).issubset(metric_ids)
    ]
