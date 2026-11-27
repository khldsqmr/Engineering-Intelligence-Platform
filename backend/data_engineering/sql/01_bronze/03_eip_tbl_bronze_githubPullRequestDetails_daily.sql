-- =====================================================================
-- Engineering Intelligence Platform (EIP)
-- Object Name : eip_tbl_bronze_githubPullRequestDetails_daily
-- Object Type : Physical Table
-- Layer       : Bronze
-- Source      : SRC-003 | GitHub Pull Request Detail API
-- Grain       : One detailed pull request observation
--
-- Purpose:
-- Preserve detailed pull request attributes required for
-- code change size and engineering activity analysis.
-- =====================================================================

CREATE TABLE IF NOT EXISTS
    eip_tbl_bronze_githubPullRequestDetails_daily (

    bronzeRecordId INTEGER PRIMARY KEY,  -- Internal observation ID

    repositoryId INTEGER NOT NULL,       -- Parent repository ID
    sourceRecordId INTEGER,              -- GitHub pull request ID
    pullRequestNumber INTEGER NOT NULL,  -- Requested PR number

    rawPayload TEXT NOT NULL             -- Original source JSON
        CHECK (json_valid(rawPayload)),

    ingestionRunId TEXT NOT NULL,        -- Parent ingestion execution
    ingestedAt TEXT NOT NULL,            -- UTC ingestion timestamp

    FOREIGN KEY (ingestionRunId)
        REFERENCES eip_tbl_control_ingestionRunHistory_log (
            ingestionRunId
        )

) STRICT;