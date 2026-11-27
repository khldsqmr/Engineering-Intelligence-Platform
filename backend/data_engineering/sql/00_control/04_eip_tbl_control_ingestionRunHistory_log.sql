-- =====================================================================
-- Engineering Intelligence Platform (EIP)
-- Layer   : Control
-- Object  : Ingestion Run History
-- Grain   : One record per ingestion execution
--
-- Purpose:
-- Track ingestion status, source coverage and API consumption.
-- =====================================================================

CREATE TABLE IF NOT EXISTS eip_tbl_control_ingestionRunHistory_log (

    ingestionRunId TEXT PRIMARY KEY NOT NULL, -- Execution UUID
    repositoryFullName TEXT NOT NULL,         -- Repository name
    repositoryId INTEGER,                    -- Resolved repository ID

    startedAt TEXT NOT NULL,                  -- Execution start
    completedAt TEXT,                         -- Execution completion

    runStatus TEXT NOT NULL CHECK (
        runStatus IN ('RUNNING', 'SUCCEEDED', 'PARTIAL', 'FAILED')
    ),

    apiRequestsExecuted INTEGER NOT NULL DEFAULT 0,
    recordsRetrieved INTEGER NOT NULL DEFAULT 0,

    coverageStartAt TEXT,
    coverageEndAt TEXT,
    enrichmentStartAt TEXT,

    coverageStatus TEXT NOT NULL DEFAULT 'UNKNOWN'
        CHECK (coverageStatus IN ('UNKNOWN', 'ESTIMATED', 'PARTIAL')),

    errorMessage TEXT                         -- Sanitized error message

) STRICT;