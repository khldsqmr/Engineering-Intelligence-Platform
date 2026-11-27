-- =====================================================================
-- Engineering Intelligence Platform (EIP)
-- =====================================================================
-- Object Name   : eip_vw_control_metricRegistry_static
-- Object Type   : View
-- Layer         : Control
-- Subject Area  : Analytical Metric Registry
-- Grain         : One record per analytical metric
-- Dependencies  : Logical dependency on source registry
-- Refresh Type  : Static, version-controlled
-- Metric Version: 1.0.0
--
-- Purpose:
-- Centralize analytical metric definitions, calculation semantics,
-- reporting cohorts, source dependencies, enrichment requirements
-- and interpretation guidelines.
--
-- Consumers:
-- 1. Gold analytical transformations.
-- 2. Deterministic insights API.
-- 3. AI context and reasoning engine.
-- 4. Evidence validation components.
-- 5. Frontend dashboards.
--
-- Design Notes:
-- 1. All reporting periods use inclusive start and exclusive end.
-- 2. All lifecycle durations represent elapsed calendar time.
-- 3. Missing source enrichment must not be interpreted as zero.
-- 4. Calculation definitions are descriptive metadata, not executable SQL.
-- 5. Historical benchmark eligibility does not guarantee availability.
-- 6. Performance direction is interpretive, not a causal conclusion.
-- 7. Metric values must be calculated deterministically outside the LLM.
-- =====================================================================


-- ---------------------------------------------------------------------
-- 01. Remove existing view definition
-- ---------------------------------------------------------------------

DROP VIEW IF EXISTS eip_vw_control_metricRegistry_static;


-- ---------------------------------------------------------------------
-- 02. Define analytical metric registry
-- ---------------------------------------------------------------------

CREATE VIEW eip_vw_control_metricRegistry_static AS

WITH metricRegistry (

    metricId,                       -- Stable analytical identifier
    metricName,                     -- Human-readable metric name
    metricCategory,                 -- Functional analytical category
    metricDescription,              -- Business meaning of the metric
    calculationDefinition,          -- Deterministic calculation semantics
    metricUnit,                     -- Unit of measurement
    aggregationType,                -- Statistical aggregation method
    analyticalCohort,               -- Eligible PR population
    periodEventAttribute,           -- Timestamp assigning PR to period
    sourceDependencies,             -- Comma-separated source identifiers
    requiresDetailEnrichment,       -- PR detail extraction requirement
    requiresReviewEnrichment,       -- Complete review extraction requirement
    performanceDirection,           -- Preferred interpretation of movement
    supportsHistoricalBenchmark,    -- Historical benchmark eligibility
    interpretationGuidance,         -- Context and analytical limitations
    displaySequence,                -- Recommended presentation order
    isActive                        -- Metric activation indicator

) AS (

    VALUES

    -- ================================================================
    -- LIFECYCLE | Pull request creation, closure and merge performance
    -- ================================================================

    (
        'prsOpened',
        'Pull Requests Opened',
        'LIFECYCLE',
        'Number of observed pull requests created during the period',
        'Count distinct PR IDs with createdAt within the reporting period',
        'COUNT',
        'COUNT_DISTINCT',
        'CREATED_IN_PERIOD',
        'createdAt',
        'SRC-002',
        0,
        0,
        'CONTEXT_DEPENDENT',
        1,
        'Measures incoming PR volume, not individual productivity',
        1,
        1
    ),

    (
        'prsMerged',
        'Pull Requests Merged',
        'LIFECYCLE',
        'Number of observed pull requests successfully merged',
        'Count distinct PR IDs with mergedAt within the reporting period',
        'COUNT',
        'COUNT_DISTINCT',
        'MERGED_IN_PERIOD',
        'mergedAt',
        'SRC-002',
        0,
        0,
        'HIGHER_IS_BETTER',
        1,
        'Measures observed merge throughput; interpret with demand and PR size',
        2,
        1
    ),

    (
        'prsClosed',
        'Pull Requests Closed',
        'LIFECYCLE',
        'Number of observed pull requests closed during the period',
        'Count distinct PR IDs with closedAt within the reporting period',
        'COUNT',
        'COUNT_DISTINCT',
        'CLOSED_IN_PERIOD',
        'closedAt',
        'SRC-002',
        0,
        0,
        'CONTEXT_DEPENDENT',
        1,
        'Includes merged and unmerged closures; not a complete closure event log',
        3,
        1
    ),

    (
        'prsClosedWithoutMerge',
        'Pull Requests Closed Without Merge',
        'LIFECYCLE',
        'Number of observed closures without a successful merge',
        'Count distinct PR IDs with closedAt in period and mergedAt null',
        'COUNT',
        'COUNT_DISTINCT',
        'CLOSED_WITHOUT_MERGE_IN_PERIOD',
        'closedAt',
        'SRC-002',
        0,
        0,
        'CONTEXT_DEPENDENT',
        1,
        'Closures may reflect duplicates, withdrawn work or obsolete changes',
        4,
        1
    ),

    (
        'medianMergeHours',
        'Median Merge Duration',
        'LIFECYCLE',
        'Median elapsed time from PR creation to successful merge',
        'Median of valid mergeHours for PRs merged during the period',
        'HOURS',
        'MEDIAN',
        'MERGED_IN_PERIOD',
        'mergedAt',
        'SRC-002',
        0,
        0,
        'LOWER_IS_BETTER',
        1,
        'Includes draft time, waiting time, weekends and inactive periods',
        5,
        1
    ),

    (
        'p90MergeHours',
        'P90 Merge Duration',
        'LIFECYCLE',
        '90th percentile of elapsed pull request merge duration',
        '90th percentile of valid mergeHours using linear interpolation',
        'HOURS',
        'PERCENTILE_90',
        'MERGED_IN_PERIOD',
        'mergedAt',
        'SRC-002',
        0,
        0,
        'LOWER_IS_BETTER',
        1,
        'Represents the slower end of observed merge durations',
        6,
        1
    ),

    -- ================================================================
    -- COLLABORATION | Review participation and lifecycle timing
    -- ================================================================

    (
        'medianFirstReviewHours',
        'Median Time to First External Review',
        'COLLABORATION',
        'Median elapsed time from creation to first qualifying external review',
        'Median of valid preReviewHours for reviewed PRs merged in period',
        'HOURS',
        'MEDIAN',
        'REVIEWED_MERGED_IN_PERIOD',
        'mergedAt',
        'SRC-002,SRC-004',
        0,
        1,
        'LOWER_IS_BETTER',
        1,
        'Measures creation-to-review elapsed time, not review-ready waiting time',
        7,
        1
    ),

    (
        'meanPreReviewHours',
        'Mean Pre-Review Duration',
        'COLLABORATION',
        'Average elapsed duration before the first qualifying external review',
        'Arithmetic mean of valid preReviewHours for reviewed merged PRs',
        'HOURS',
        'MEAN',
        'REVIEWED_MERGED_IN_PERIOD',
        'mergedAt',
        'SRC-002,SRC-004',
        0,
        1,
        'LOWER_IS_BETTER',
        1,
        'Includes author preparation, draft time and reviewer waiting time',
        8,
        1
    ),

    (
        'meanPostReviewHours',
        'Mean Post-Review Duration',
        'COLLABORATION',
        'Average elapsed duration from first external review to merge',
        'Arithmetic mean of valid postReviewHours for reviewed merged PRs',
        'HOURS',
        'MEAN',
        'REVIEWED_MERGED_IN_PERIOD',
        'mergedAt',
        'SRC-002,SRC-004',
        0,
        1,
        'LOWER_IS_BETTER',
        1,
        'Includes revisions, additional reviews, approvals and merge waiting',
        9,
        1
    ),

    (
        'preReviewTimeSharePct',
        'Pre-Review Time Share',
        'COLLABORATION',
        'Share of elapsed merge duration occurring before first external review',
        '100 times sum of preReviewHours divided by sum of mergeHours',
        'PERCENT',
        'RATIO_OF_SUMS',
        'REVIEWED_MERGED_IN_PERIOD',
        'mergedAt',
        'SRC-002,SRC-004',
        0,
        1,
        'CONTEXT_DEPENDENT',
        1,
        'Uses the same reviewed merged cohort in numerator and denominator',
        10,
        1
    ),

    (
        'mergedPRReviewCoveragePct',
        'Merged PR External Review Coverage',
        'COLLABORATION',
        'Percentage of observed merged PRs with a qualifying external review',
        '100 times reviewed merged PRs divided by all eligible merged PRs',
        'PERCENT',
        'RATIO_OF_COUNTS',
        'MERGED_IN_PERIOD',
        'mergedAt',
        'SRC-002,SRC-004',
        0,
        1,
        'CONTEXT_DEPENDENT',
        1,
        'Publish full-cohort ratio only when review extraction is complete',
        11,
        1
    ),

    (
        'uniqueExternalReviewers',
        'Unique External Reviewers',
        'COLLABORATION',
        'Number of distinct qualifying external reviewer accounts',
        'Count distinct reviewer IDs across qualifying reviews of merged PRs',
        'COUNT',
        'COUNT_DISTINCT',
        'MERGED_IN_PERIOD',
        'mergedAt',
        'SRC-002,SRC-004',
        0,
        1,
        'CONTEXT_DEPENDENT',
        1,
        'Counts distinct accounts, not review events or individual workload',
        12,
        1
    ),

    -- ================================================================
    -- CODE CHANGE | Change size and scope
    -- ================================================================

    (
        'medianLinesChanged',
        'Median Lines Changed',
        'CODE_CHANGE',
        'Median number of added and deleted lines per merged pull request',
        'Median of additionsCount plus deletionsCount for enriched merged PRs',
        'LINES',
        'MEDIAN',
        'MERGED_IN_PERIOD',
        'mergedAt',
        'SRC-002,SRC-003',
        1,
        0,
        'CONTEXT_DEPENDENT',
        1,
        'Change size is a proxy for scope, not a direct complexity measure',
        13,
        1
    ),

    (
        'medianFilesChanged',
        'Median Files Changed',
        'CODE_CHANGE',
        'Median number of changed files per merged pull request',
        'Median of changedFilesCount for enriched merged PRs',
        'FILES',
        'MEDIAN',
        'MERGED_IN_PERIOD',
        'mergedAt',
        'SRC-002,SRC-003',
        1,
        0,
        'CONTEXT_DEPENDENT',
        1,
        'Measures change breadth, not engineering effort or code quality',
        14,
        1
    )

)


-- ---------------------------------------------------------------------
-- 03. Expose metric definitions
-- ---------------------------------------------------------------------

SELECT
    metricId,
    metricName,
    metricCategory,
    metricDescription,
    calculationDefinition,
    metricUnit,
    aggregationType,
    analyticalCohort,
    periodEventAttribute,
    sourceDependencies,
    requiresDetailEnrichment,
    requiresReviewEnrichment,
    performanceDirection,
    supportsHistoricalBenchmark,
    interpretationGuidance,
    '1.0.0' AS metricVersion,
    displaySequence,
    isActive

FROM metricRegistry;