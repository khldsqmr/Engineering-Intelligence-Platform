-- =====================================================================
-- Engineering Intelligence Platform (EIP)
-- Object Name : eip_tbl_gold_periodFacts_long
-- Object Type : Physical Table
-- Layer       : Gold
-- Grain       : Repository, reporting period, metric and version
-- Sources     : Gold PR Lifecycle and Control Metric Registry
--
-- Purpose:
-- Persist deterministic period metrics, comparative analytics,
-- historical benchmarks, coverage and traceable evidence.
--
-- Reporting boundaries:
-- periodStart        : Inclusive UTC calendar date
-- periodEndExclusive : Exclusive UTC calendar date
-- =====================================================================

CREATE TABLE IF NOT EXISTS eip_tbl_gold_periodFacts_long (

    -- 01. Reporting dimensions

    repositoryId INTEGER NOT NULL,
    periodType TEXT NOT NULL,
    periodStart TEXT NOT NULL,
    periodEndExclusive TEXT NOT NULL,

    -- 02. Metric metadata

    metricId TEXT NOT NULL,
    metricVersion TEXT NOT NULL,
    metricUnit TEXT NOT NULL,

    -- 03. Period comparison

    currentValue REAL,
    previousValue REAL,
    changeValue REAL,
    changePct REAL,

    -- 04. Historical benchmark

    historicalBenchmarkAvg REAL,
    historicalBenchmarkStd REAL,
    changeVsBenchmarkPct REAL,
    benchmarkPeriodCount INTEGER NOT NULL DEFAULT 0,

    -- 05. Current-period analytical coverage

    eligiblePRCount INTEGER,
    enrichedPRCount INTEGER,
    sampleSize INTEGER,

    enrichmentCoveragePct REAL
        CHECK (enrichmentCoveragePct BETWEEN 0 AND 100),

    coverageStatus TEXT NOT NULL,

    -- 06. Previous-period analytical coverage

    previousSampleSize INTEGER,
    previousEnrichmentCoveragePct REAL,
    previousCoverageStatus TEXT NOT NULL,

    -- 07. Evidence and operational lineage

    evidenceId TEXT NOT NULL UNIQUE,
    ingestionRunId TEXT NOT NULL,
    calculatedAt TEXT NOT NULL,

    PRIMARY KEY (
        repositoryId,
        periodType,
        periodStart,
        periodEndExclusive,
        metricId,
        metricVersion
    ),

    FOREIGN KEY (ingestionRunId)
        REFERENCES eip_tbl_control_ingestionRunHistory_log(ingestionRunId),

    CHECK (periodEndExclusive > periodStart)

) STRICT;