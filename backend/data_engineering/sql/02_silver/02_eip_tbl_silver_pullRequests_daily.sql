-- =====================================================================
-- Engineering Intelligence Platform (EIP)
-- Object Name : eip_tbl_silver_pullRequests_daily
-- Object Type : Physical Table
-- Layer       : Silver
-- Sources     : SRC-002, SRC-003
-- Grain       : One record per repository and pull request
--
-- Purpose:
-- Consolidate validated PR lifecycle and detail attributes.
-- =====================================================================

CREATE TABLE IF NOT EXISTS eip_tbl_silver_pullRequests_daily (

    -- 01. Entity identifiers

    repositoryId INTEGER NOT NULL,
    pullRequestId INTEGER NOT NULL,
    pullRequestNumber INTEGER NOT NULL,

    -- 02. Pull request status

    pullRequestState TEXT NOT NULL
        CHECK (pullRequestState IN ('open', 'closed')),

    isDraft INTEGER CHECK (isDraft IN (0, 1)),
    isMerged INTEGER NOT NULL CHECK (isMerged IN (0, 1)),

    -- 03. Author attributes

    authorId INTEGER,
    authorName TEXT,
    authorType TEXT,
    authorAssociation TEXT,

    -- 04. Lifecycle timestamps

    createdAt TEXT NOT NULL,
    updatedAt TEXT NOT NULL,
    closedAt TEXT,
    mergedAt TEXT,

    -- 05. Branch and source attributes

    targetBranch TEXT,
    sourceBranch TEXT,
    pullRequestUrl TEXT,

    -- 06. Detailed code change attributes

    additionsCount INTEGER CHECK (additionsCount >= 0),
    deletionsCount INTEGER CHECK (deletionsCount >= 0),
    changedFilesCount INTEGER CHECK (changedFilesCount >= 0),

    commitsCount INTEGER CHECK (commitsCount >= 0),
    commentsCount INTEGER CHECK (commentsCount >= 0),
    reviewCommentsCount INTEGER CHECK (reviewCommentsCount >= 0),

    mergedById INTEGER,
    mergedByName TEXT,

    -- 07. Enrichment completeness

    isDetailExtractionComplete INTEGER NOT NULL DEFAULT 0
        CHECK (isDetailExtractionComplete IN (0, 1)),

    isReviewExtractionComplete INTEGER NOT NULL DEFAULT 0
        CHECK (isReviewExtractionComplete IN (0, 1)),

    detailExtractedAt TEXT,
    reviewExtractedAt TEXT,

    -- 08. Operational lineage

    ingestionRunId TEXT NOT NULL,
    bronzeRecordId INTEGER NOT NULL,
    detailBronzeRecordId INTEGER,
    processedAt TEXT NOT NULL,

    -- 09. Entity integrity

    PRIMARY KEY (repositoryId, pullRequestId),

    UNIQUE (repositoryId, pullRequestNumber),

    FOREIGN KEY (repositoryId)
        REFERENCES eip_tbl_silver_repositories_daily(repositoryId),

    FOREIGN KEY (ingestionRunId)
        REFERENCES eip_tbl_control_ingestionRunHistory_log(ingestionRunId),

    CHECK (updatedAt >= createdAt),
    CHECK (closedAt IS NULL OR closedAt >= createdAt),
    CHECK (mergedAt IS NULL OR mergedAt >= createdAt),

    CHECK (
        (isMerged = 0 AND mergedAt IS NULL)
        OR
        (isMerged = 1 AND mergedAt IS NOT NULL)
    )

) STRICT;