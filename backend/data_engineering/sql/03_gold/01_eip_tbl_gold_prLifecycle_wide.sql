-- =====================================================================
-- Engineering Intelligence Platform (EIP)
-- Object Name : eip_tbl_gold_prLifecycle_wide
-- Object Type : Physical Table
-- Layer       : Gold
-- Grain       : One record per repository and pull request
-- Sources     : Silver Pull Requests and Silver Reviews
--
-- Purpose:
-- Calculate deterministic PR lifecycle, collaboration and
-- code change attributes for downstream period analytics.
-- =====================================================================

CREATE TABLE IF NOT EXISTS eip_tbl_gold_prLifecycle_wide (

    -- 01. Entity identifiers

    repositoryId INTEGER NOT NULL,
    pullRequestId INTEGER NOT NULL,
    pullRequestNumber INTEGER NOT NULL,
    authorId INTEGER,

    -- 02. Pull request status

    pullRequestState TEXT NOT NULL,
    isDraft INTEGER,
    isMerged INTEGER NOT NULL,

    -- 03. Lifecycle timestamps

    createdAt TEXT NOT NULL,
    closedAt TEXT,
    mergedAt TEXT,
    firstReviewAt TEXT,
    lastReviewAt TEXT,

    -- 04. Collaboration measures

    externalReviewCount INTEGER,
    uniqueExternalReviewerCount INTEGER,

    -- Distinct reviewer IDs for period-level deduplication.
    externalReviewerIdsJson TEXT
        CHECK (
            externalReviewerIdsJson IS NULL
            OR json_valid(externalReviewerIdsJson)
        ),

    -- 05. Code change measures

    linesChanged INTEGER,
    changedFilesCount INTEGER,

    -- 06. Lifecycle duration measures

    mergeHours REAL CHECK (mergeHours >= 0),
    preReviewHours REAL CHECK (preReviewHours >= 0),
    postReviewHours REAL CHECK (postReviewHours >= 0),

    preReviewTimeSharePct REAL
        CHECK (preReviewTimeSharePct BETWEEN 0 AND 100),

    -- 07. Enrichment completeness

    isDetailExtractionComplete INTEGER NOT NULL
        CHECK (isDetailExtractionComplete IN (0, 1)),

    isReviewExtractionComplete INTEGER NOT NULL
        CHECK (isReviewExtractionComplete IN (0, 1)),

    -- 08. Operational lineage

    ingestionRunId TEXT NOT NULL,
    calculatedAt TEXT NOT NULL,

    PRIMARY KEY (repositoryId, pullRequestId),

    FOREIGN KEY (ingestionRunId)
        REFERENCES eip_tbl_control_ingestionRunHistory_log(ingestionRunId)

) STRICT;