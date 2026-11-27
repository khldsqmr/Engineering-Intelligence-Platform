-- =====================================================================
-- Engineering Intelligence Platform (EIP)
-- Object Name : eip_tbl_bronze_githubRepositories_daily
-- Object Type : Physical Table
-- Layer       : Bronze
-- Source      : SRC-001 | GitHub Repository API
-- Grain       : One repository observation per extraction
--
-- Purpose:
-- Preserve original GitHub repository metadata and ingestion lineage.
-- =====================================================================

CREATE TABLE IF NOT EXISTS eip_tbl_bronze_githubRepositories_daily (

    bronzeRecordId INTEGER PRIMARY KEY,  -- Internal observation ID

    repositoryId INTEGER NOT NULL,       -- GitHub repository ID
    sourceRecordId INTEGER,              -- Original source identifier

    rawPayload TEXT NOT NULL             -- Original source JSON
        CHECK (json_valid(rawPayload)),

    ingestionRunId TEXT NOT NULL,        -- Parent ingestion execution
    ingestedAt TEXT NOT NULL,            -- UTC ingestion timestamp

    FOREIGN KEY (ingestionRunId)
        REFERENCES eip_tbl_control_ingestionRunHistory_log (
            ingestionRunId
        )

) STRICT;