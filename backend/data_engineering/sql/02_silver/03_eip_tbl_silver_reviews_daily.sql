-- =====================================================================
-- Engineering Intelligence Platform (EIP)
-- Object Name : eip_tbl_silver_reviews_daily
-- Object Type : Physical Table
-- Layer       : Silver
-- Source      : SRC-004
-- Grain       : One record per repository, PR and review
--
-- Purpose:
-- Maintain standardized pull request review observations.
-- =====================================================================

CREATE TABLE IF NOT EXISTS eip_tbl_silver_reviews_daily (

    repositoryId INTEGER NOT NULL,       -- Parent repository ID
    pullRequestId INTEGER NOT NULL,       -- Parent PR ID
    pullRequestNumber INTEGER NOT NULL,   -- Repository-specific PR number
    reviewId INTEGER NOT NULL,            -- GitHub review identifier

    reviewerId INTEGER,                  -- Reviewer account ID
    reviewerName TEXT,                    -- Reviewer account name
    reviewerType TEXT,                    -- GitHub account type

    reviewState TEXT NOT NULL,            -- Observed review state
    submittedAt TEXT,                     -- Review submission timestamp
    reviewerAssociation TEXT,            -- Repository relationship
    reviewedCommitId TEXT,                -- Reviewed commit identifier
    reviewUrl TEXT,                       -- GitHub review URL

    ingestionRunId TEXT NOT NULL,         -- Source execution
    bronzeRecordId INTEGER NOT NULL,      -- Bronze observation lineage
    processedAt TEXT NOT NULL,            -- Silver processing time

    PRIMARY KEY (
        repositoryId,
        pullRequestId,
        reviewId
    ),

    FOREIGN KEY (repositoryId, pullRequestId)
        REFERENCES eip_tbl_silver_pullRequests_daily(
            repositoryId,
            pullRequestId
        ),

    FOREIGN KEY (ingestionRunId)
        REFERENCES eip_tbl_control_ingestionRunHistory_log(ingestionRunId)

) STRICT;