-- =====================================================================
-- Engineering Intelligence Platform (EIP)
-- Object Name : eip_tbl_bronze_githubReviews_daily
-- Object Type : Physical Table
-- Layer       : Bronze
-- Source      : SRC-004 | GitHub Pull Request Reviews API
-- Grain       : One review observation associated with a PR
--
-- Purpose:
-- Preserve original review records for collaboration analysis,
-- review participation and pull request lifecycle measurements.
-- =====================================================================

CREATE TABLE IF NOT EXISTS eip_tbl_bronze_githubReviews_daily (

    bronzeRecordId INTEGER PRIMARY KEY,  -- Internal observation ID

    repositoryId INTEGER NOT NULL,       -- Parent repository ID
    sourceRecordId INTEGER,              -- GitHub review ID

    pullRequestId INTEGER NOT NULL,       -- Parent pull request ID
    pullRequestNumber INTEGER NOT NULL,   -- Parent PR number

    rawPayload TEXT NOT NULL             -- Original source JSON
        CHECK (json_valid(rawPayload)),

    ingestionRunId TEXT NOT NULL,        -- Parent ingestion execution
    ingestedAt TEXT NOT NULL,            -- UTC ingestion timestamp

    FOREIGN KEY (ingestionRunId)
        REFERENCES eip_tbl_control_ingestionRunHistory_log (
            ingestionRunId
        )

) STRICT;