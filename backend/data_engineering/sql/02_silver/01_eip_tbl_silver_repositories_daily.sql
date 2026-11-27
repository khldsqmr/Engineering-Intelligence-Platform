-- =====================================================================
-- Engineering Intelligence Platform (EIP)
-- Object Name : eip_tbl_silver_repositories_daily
-- Object Type : Physical Table
-- Layer       : Silver
-- Source      : SRC-001
-- Grain       : One record per repository
--
-- Purpose:
-- Maintain standardized GitHub repository metadata.
-- =====================================================================

CREATE TABLE IF NOT EXISTS eip_tbl_silver_repositories_daily (

    repositoryId INTEGER PRIMARY KEY,       -- GitHub repository ID
    repositoryName TEXT NOT NULL,           -- Repository name
    repositoryFullName TEXT NOT NULL,       -- Owner-qualified name

    ownerId INTEGER,                        -- Repository owner ID
    ownerName TEXT,                         -- Owner account name
    repositoryDescription TEXT,             -- Repository description

    primaryLanguage TEXT,                   -- Primary programming language
    defaultBranch TEXT,                     -- Default branch

    createdAt TEXT,                         -- Repository creation time
    updatedAt TEXT,                         -- Source update time
    pushedAt TEXT,                          -- Latest push time

    starsCount INTEGER,                     -- GitHub stars
    forksCount INTEGER,                     -- Repository forks
    openIssuesCount INTEGER,                -- Open issues including PRs

    isArchived INTEGER CHECK (isArchived IN (0, 1)),
    isPrivate INTEGER CHECK (isPrivate IN (0, 1)),

    repositoryUrl TEXT,                     -- GitHub repository URL

    ingestionRunId TEXT NOT NULL,           -- Source execution
    bronzeRecordId INTEGER NOT NULL,        -- Bronze observation lineage
    processedAt TEXT NOT NULL,              -- Silver processing time

    FOREIGN KEY (ingestionRunId)
        REFERENCES eip_tbl_control_ingestionRunHistory_log(ingestionRunId)

) STRICT;