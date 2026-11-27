-- =====================================================================
-- Engineering Intelligence Platform (EIP)
-- Object Name : eip_tbl_bronze_githubPullRequests_daily
-- Object Type : Physical Table
-- Layer       : Bronze
-- Source      : SRC-002 | GitHub Pull Request List API
-- Grain       : One pull request observation
--
-- Purpose:
-- Preserve original pull request list records for subsequent
-- lifecycle analysis, validation and standardization.
-- =====================================================================

CREATE TABLE IF NOT EXISTS eip_tbl_bronze_githubPullRequests_daily (

    bronzeRecordId INTEGER PRIMARY KEY,  -- Internal observation ID

    repositoryId INTEGER NOT NULL,       -- Parent repository ID
    sourceRecordId INTEGER,              -- GitHub pull request ID
    pullRequestNumber INTEGER,           -- Repository-specific PR number

    rawPayload TEXT NOT NULL             -- Original source JSON
        CHECK (json_valid(rawPayload)),

    ingestionRunId TEXT NOT NULL,        -- Parent ingestion execution
    ingestedAt TEXT NOT NULL,            -- UTC ingestion timestamp

    FOREIGN KEY (ingestionRunId)
        REFERENCES eip_tbl_control_ingestionRunHistory_log (
            ingestionRunId
        )

) STRICT;