-- =====================================================================
-- Engineering Intelligence Platform (EIP)
-- =====================================================================
-- Object Name   : eip_vw_control_sourceRegistry_static
-- Object Type   : View
-- Layer         : Control
-- Subject Area  : Source Registry
-- Grain         : One record per registered source dataset
-- Source System : GitHub REST API
-- Dependencies  : None
-- Refresh Type  : Static, version-controlled
--
-- Purpose:
-- Centralize source dataset definitions, endpoint templates,
-- ingestion strategies, source identifiers and Bronze targets.
--
-- Design Notes:
-- 1. Source identifiers remain stable across pipeline executions.
-- 2. Endpoint templates contain no credentials.
-- 3. Runtime endpoint construction must validate input parameters.
-- 4. Historical lookback and request limits are maintained separately
--    in the pipeline configuration control view.
-- 5. Bronze table names represent planned physical ingestion targets.
-- =====================================================================


-- ---------------------------------------------------------------------
-- 01. Remove existing view definition
-- ---------------------------------------------------------------------

DROP VIEW IF EXISTS eip_vw_control_sourceRegistry_static;


-- ---------------------------------------------------------------------
-- 02. Create source registry
-- ---------------------------------------------------------------------

CREATE VIEW eip_vw_control_sourceRegistry_static AS

WITH sourceRegistry (

    sourceId,                   -- Stable source dataset identifier
    sourceSystem,               -- External source platform
    sourceEntity,               -- Source dataset entity name
    sourceDescription,          -- Business and technical description
    sourceBaseUrl,              -- Approved source API base URL
    sourceEndpointTemplate,     -- Relative API endpoint template
    httpMethod,                 -- HTTP request method
    authenticationType,         -- Source authentication mechanism
    sourceRecordKey,            -- Primary identifier in source payload
    parentSourceId,             -- Logical parent source identifier
    sourceUpdatedAttribute,     -- Source update watermark attribute
    sourceEventAttribute,       -- Relevant source event timestamp
    paginationType,             -- Source pagination mechanism
    extractionStrategy,         -- Logical ingestion strategy
    targetBronzeTable,          -- Physical Bronze destination
    executionSequence,          -- Logical extraction dependency order
    isActive                    -- Source activation indicator

) AS (

    VALUES

    -- ================================================================
    -- SRC-001 | GitHub Repository Metadata
    -- ================================================================

    (
        'SRC-001',
        'GitHub',
        'Repository',
        'Repository metadata and current repository attributes',
        'https://api.github.com',
        '/repos/{owner}/{repo}',
        'GET',
        'BEARER_TOKEN',
        'id',
        NULL,
        'updated_at',
        NULL,
        'NONE',
        'CURRENT_SNAPSHOT',
        'eip_tbl_bronze_githubRepositories_daily',
        1,
        1
    ),

    -- ================================================================
    -- SRC-002 | GitHub Pull Requests
    -- ================================================================

    (
        'SRC-002',
        'GitHub',
        'PullRequest',
        'Pull request lifecycle and author attributes',
        'https://api.github.com',
        '/repos/{owner}/{repo}/pulls',
        'GET',
        'BEARER_TOKEN',
        'id',
        'SRC-001',
        'updated_at',
        NULL,
        'PAGE_NUMBER',
        'BOUNDED_UPDATE_WINDOW',
        'eip_tbl_bronze_githubPullRequests_daily',
        2,
        1
    ),

    -- ================================================================
    -- SRC-003 | GitHub Pull Request Details
    -- ================================================================

    (
        'SRC-003',
        'GitHub',
        'PullRequestDetail',
        'Detailed pull request statistics and code change attributes',
        'https://api.github.com',
        '/repos/{owner}/{repo}/pulls/{pullRequestNumber}',
        'GET',
        'BEARER_TOKEN',
        'id',
        'SRC-002',
        'updated_at',
        'merged_at',
        'NONE',
        'MERGED_COHORT_ENRICHMENT',
        'eip_tbl_bronze_githubPullRequestDetails_daily',
        3,
        1
    ),

    -- ================================================================
    -- SRC-004 | GitHub Pull Request Reviews
    -- ================================================================

    (
        'SRC-004',
        'GitHub',
        'PullRequestReview',
        'Submitted pull request reviews and reviewer attributes',
        'https://api.github.com',
        '/repos/{owner}/{repo}/pulls/{pullRequestNumber}/reviews',
        'GET',
        'BEARER_TOKEN',
        'id',
        'SRC-002',
        NULL,
        'submitted_at',
        'PAGE_NUMBER',
        'MERGED_COHORT_ENRICHMENT',
        'eip_tbl_bronze_githubReviews_daily',
        4,
        1
    )

)


-- ---------------------------------------------------------------------
-- 03. Expose registered source definitions
-- ---------------------------------------------------------------------

SELECT
    sourceId,
    sourceSystem,
    sourceEntity,
    sourceDescription,
    sourceBaseUrl,
    sourceEndpointTemplate,
    httpMethod,
    authenticationType,
    sourceRecordKey,
    parentSourceId,
    sourceUpdatedAttribute,
    sourceEventAttribute,
    paginationType,
    extractionStrategy,
    targetBronzeTable,
    executionSequence,
    isActive

FROM sourceRegistry;