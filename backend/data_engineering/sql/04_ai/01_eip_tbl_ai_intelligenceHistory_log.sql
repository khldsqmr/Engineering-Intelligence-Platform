-- Engineering Intelligence Platform
-- Layer: AI Intelligence
-- Grain: One record per intelligence execution
-- Purpose: Audit, governance and historical context retrieval

CREATE TABLE IF NOT EXISTS eip_tbl_ai_intelligenceHistory_log (

    -- 01. Identification and temporal context
    intelligenceId TEXT PRIMARY KEY,
    repositoryId INTEGER NOT NULL,
    repository TEXT NOT NULL,
    ingestionRunId TEXT NOT NULL,

    periodStart TEXT NOT NULL,
    periodEndExclusive TEXT NOT NULL,

    intelligenceMode TEXT NOT NULL
        CHECK (intelligenceMode IN ('narrative', 'question')),

    -- 02. Context and evidence lineage
    contextVersion TEXT NOT NULL,
    contextSnapshotJson TEXT NOT NULL
        CHECK (json_valid(contextSnapshotJson)),

    modelInputJson TEXT
        CHECK (modelInputJson IS NULL OR json_valid(modelInputJson)),

    metricVersionsJson TEXT NOT NULL
        CHECK (json_valid(metricVersionsJson)),

    historicalIntelligenceIdsJson TEXT NOT NULL
        CHECK (json_valid(historicalIntelligenceIdsJson)),

    -- 03. Generated intelligence
    responseStatus TEXT,

    responseJson TEXT
        CHECK (responseJson IS NULL OR json_valid(responseJson)),

    narrative TEXT,
    hypothesis TEXT,

    -- 04. Generator metadata
    generatorModel TEXT NOT NULL,
    generatorPromptVersion TEXT,

    generationLatencySeconds REAL,
    generationInputTokens INTEGER,
    generationOutputTokens INTEGER,

    -- 05. Evaluation metadata
    evaluationVersion TEXT NOT NULL,
    evaluatorModel TEXT,
    evaluatorPromptVersion TEXT,
    evaluatorLatencySeconds REAL,

    evaluationScore REAL
        CHECK (evaluationScore BETWEEN 0 AND 100),

    evaluationJson TEXT NOT NULL
        CHECK (json_valid(evaluationJson)),

    -- 06. Hypothesis confidence
    confidenceVersion TEXT,

    confidenceScore REAL
        CHECK (confidenceScore BETWEEN 0 AND 100),

    confidenceJson TEXT
        CHECK (confidenceJson IS NULL OR json_valid(confidenceJson)),

    -- 07. Automated governance
    approvalStatus TEXT NOT NULL
        CHECK (approvalStatus IN (
            'AUTO_APPROVED',
            'REGENERATE',
            'REJECTED',
            'EVALUATION_FAILED'
        )),

    deterministicValidationPassed INTEGER NOT NULL
        CHECK (deterministicValidationPassed IN (0, 1)),

    eligibleForHistoricalContext INTEGER NOT NULL DEFAULT 0
        CHECK (eligibleForHistoricalContext IN (0, 1)),

    -- 08. Operational metadata
    createdAt TEXT NOT NULL,

    CHECK (periodStart < periodEndExclusive),

    CHECK (
        eligibleForHistoricalContext = 0
        OR (
            approvalStatus = 'AUTO_APPROVED'
            AND deterministicValidationPassed = 1
            AND intelligenceMode = 'narrative'
            AND responseStatus IS NOT NULL
            AND responseStatus = 'ANSWERED'
            AND narrative IS NOT NULL
            AND evaluationScore IS NOT NULL
        )
    )
);


-- Historical intelligence retrieval
CREATE INDEX IF NOT EXISTS
    idx_ai_intelligenceHistory_retrieval
ON eip_tbl_ai_intelligenceHistory_log (
    repositoryId,
    eligibleForHistoricalContext,
    periodEndExclusive DESC,
    createdAt DESC
);


-- Period-based intelligence explorer
CREATE INDEX IF NOT EXISTS
    idx_ai_intelligenceHistory_period
ON eip_tbl_ai_intelligenceHistory_log (
    repositoryId,
    periodStart,
    periodEndExclusive,
    createdAt DESC
);


-- Ingestion lineage
CREATE INDEX IF NOT EXISTS
    idx_ai_intelligenceHistory_ingestionRun
ON eip_tbl_ai_intelligenceHistory_log (
    ingestionRunId
);
