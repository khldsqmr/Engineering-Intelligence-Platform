-- =====================================================================
-- Engineering Intelligence Platform (EIP)
-- =====================================================================
-- Object Name   : eip_vw_control_pipelineConfig_static
-- Object Type   : View
-- Layer         : Control
-- Subject Area  : Pipeline Configuration
-- Grain         : One record per configuration parameter
-- Dependencies  : None
-- Refresh Type  : Static, version-controlled
--
-- Purpose:
-- Centralize ingestion, API consumption, reporting and analytical
-- configuration defaults used throughout the EIP platform.
--
-- Configuration Basis:
-- GitHub historical profiling conducted on November 26, 2026.
--
-- Design Notes:
-- 1. Configuration keys remain stable across pipeline executions.
-- 2. Configuration values are stored as TEXT for consistent typing.
-- 3. Consumers must convert values using the declared data type.
-- 4. Credentials and environment-specific secrets are excluded.
-- 5. Runtime configuration overrides must be validated.
-- 6. Historical lookback values represent target coverage,
--    not guaranteed source completeness.
-- 7. Planned configuration does not imply implemented functionality.
-- =====================================================================


-- ---------------------------------------------------------------------
-- 01. Remove existing view definition
-- ---------------------------------------------------------------------

DROP VIEW IF EXISTS eip_vw_control_pipelineConfig_static;


-- ---------------------------------------------------------------------
-- 02. Define pipeline configuration registry
-- ---------------------------------------------------------------------

CREATE VIEW eip_vw_control_pipelineConfig_static AS

WITH pipelineConfig (

    configKey,                 -- Stable configuration identifier
    configCategory,            -- Functional configuration category
    configValue,               -- Default value represented as TEXT
    configDataType,            -- Declared logical value type
    configUnit,                -- Unit of measurement, where applicable
    configDescription,         -- Business and technical description
    isActive                   -- Configuration activation indicator

) AS (

    VALUES

    -- ================================================================
    -- INGESTION | Historical and incremental extraction
    -- ================================================================

    (
        'basicHistoryDays',
        'INGESTION',
        '60',
        'INTEGER',
        'DAYS',
        'Target historical lookback for basic pull request ingestion',
        1
    ),

    (
        'enrichmentHistoryDays',
        'INGESTION',
        '21',
        'INTEGER',
        'DAYS',
        'Historical lookback for detailed merged PR enrichment',
        1
    ),

    (
        'enrichmentCohort',
        'INGESTION',
        'MERGED_PULL_REQUESTS',
        'TEXT',
        NULL,
        'Pull requests merged within the enrichment reporting window',
        1
    ),

    (
        'incrementalOverlapHours',
        'INGESTION',
        '48',
        'INTEGER',
        'HOURS',
        'Proposed overlap for incremental source extraction',
        1
    ),

    -- ================================================================
    -- API | Pagination and request consumption safeguards
    -- ================================================================

    (
        'maxListPages',
        'API',
        '50',
        'INTEGER',
        'PAGES',
        'Maximum pull request list pages retrieved per scan',
        1
    ),

    (
        'recordsPerPage',
        'API',
        '100',
        'INTEGER',
        'RECORDS',
        'Requested source records per paginated API response',
        1
    ),

    (
        'maxApiRequestsPerRun',
        'API',
        '3000',
        'INTEGER',
        'REQUESTS',
        'Maximum API requests permitted per ingestion execution',
        1
    ),

    (
        'minimumApiReserve',
        'API',
        '500',
        'INTEGER',
        'REQUESTS',
        'Minimum primary GitHub API quota reserve',
        1
    ),

    (
        'boundaryConfirmationPages',
        'API',
        '2',
        'INTEGER',
        'PAGES',
        'Consecutive pages outside cutoff used for estimated coverage',
        1
    ),

    -- ================================================================
    -- REPORTING | Period definitions
    -- ================================================================

    (
        'reportingPeriodDays',
        'REPORTING',
        '7',
        'INTEGER',
        'DAYS',
        'Default rolling reporting period length',
        1
    ),

    (
        'reportingTimezone',
        'REPORTING',
        'UTC',
        'TEXT',
        NULL,
        'Standard timezone for reporting period calculations',
        1
    ),

    -- ================================================================
    -- ANALYTICS | Historical comparison parameters
    -- ================================================================

    (
        'benchmarkPeriodCount',
        'ANALYTICS',
        '2',
        'INTEGER',
        'PERIODS',
        'Number of preceding periods in historical benchmarks',
        1
    ),

    -- ================================================================
    -- PLANNING | Workload estimation parameters
    -- ================================================================

    (
        'requestContingencyPct',
        'PLANNING',
        '20',
        'REAL',
        'PERCENT',
        'Planning allowance for extra pagination and API retries',
        1
    )

)


-- ---------------------------------------------------------------------
-- 03. Expose active and inactive configuration definitions
-- ---------------------------------------------------------------------

SELECT
    configKey,
    configCategory,
    configValue,
    configDataType,
    configUnit,
    configDescription,
    isActive

FROM pipelineConfig;