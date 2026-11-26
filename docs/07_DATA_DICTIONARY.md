# Engineering Intelligence Platform (EIP)

# Data Dictionary and Source-to-Target Mappings

| Document Attribute | Value |
|---|---|
| Product | CodePulse |
| Platform | Engineering Intelligence Platform |
| Document Version | 1.0.0 |
| Database Engine | SQLite |
| Database Path | data/eip.db |
| Reporting Timezone | UTC |
| Status | Initial Data Contract |

## 1. Purpose

This document defines the platform's database objects,
column semantics, data types, entity relationships,
source lineage and analytical data contracts.

The SQL schema definitions remain the authoritative
implementation of physical database objects.

## 2. Engineering Conventions

### 2.1 Object Naming

eip_{objectType}_{layer}_{subjectArea}_{cadenceOrShape}

| Component | Description |
|---|---|
| eip | Engineering Intelligence Platform |
| tbl | Physical database table |
| vw | Database view |
| control | Configuration and operational governance |
| bronze | Original source observations |
| silver | Standardized and validated entities |
| gold | Analytical facts |
| static | Version-controlled definitions |
| daily | Intended daily refresh convention |
| current | Latest operational state |
| log | Execution or validation history |
| wide | Multiple analytical attributes per record |
| long | One metric per analytical fact record |

The daily suffix represents the intended refresh convention.
Scheduled daily execution has not yet been implemented.

### 2.2 Column Naming

Database columns and analytical metric identifiers use
lowerCamelCase.

Examples:

- repositoryId
- pullRequestId
- ingestionRunId
- firstReviewAt
- medianMergeHours
- enrichmentCoveragePct

### 2.3 SQLite Data Types

| Logical Type | SQLite Storage |
|---|---|
| Identifier | INTEGER |
| Whole number | INTEGER |
| Decimal measure | REAL |
| Boolean | INTEGER, restricted to 0 or 1 |
| String | TEXT |
| Timestamp | TEXT, canonical ISO 8601 UTC |
| Calendar date | TEXT, YYYY-MM-DD |
| JSON payload | TEXT |
| Execution identifier | TEXT, UUID |

GitHub identifiers require signed 64-bit integer storage.

All analytical timestamps must be normalized to UTC.

Timestamp serialization must use a consistent format
to support chronological comparisons.

### 2.4 Null Semantics

NULL represents unavailable, unknown, invalid or
not-applicable data according to the column definition.

Zero represents an observed numeric value of zero.

Incomplete source extraction must not be interpreted
as zero source activity.

## 3. Database Object Inventory

| Object | Type | Grain | Status |
|---|---|---|---|
| eip_vw_control_sourceRegistry_static | View | Source dataset | Validated |
| eip_vw_control_pipelineConfig_static | View | Configuration parameter | Validated |
| eip_vw_control_metricRegistry_static | View | Analytical metric | Validated |
| eip_tbl_control_ingestionRunHistory_log | Table | Ingestion execution | Planned |
| eip_tbl_control_syncState_current | Table | Repository and source | Planned |
| eip_tbl_control_dataQualityResults_log | Table | Validation result | Planned |
| eip_tbl_bronze_githubRepositories_daily | Table | Repository observation | Planned |
| eip_tbl_bronze_githubPullRequests_daily | Table | PR observation | Planned |
| eip_tbl_bronze_githubPullRequestDetails_daily | Table | PR detail observation | Planned |
| eip_tbl_bronze_githubReviews_daily | Table | Review observation | Planned |
| eip_tbl_silver_repositories_daily | Table | Repository | Planned |
| eip_tbl_silver_pullRequests_daily | Table | Repository and PR | Planned |
| eip_tbl_silver_reviews_daily | Table | Repository, PR and review | Planned |
| eip_tbl_gold_prLifecycle_wide | Table | Repository and PR | Planned |
| eip_tbl_gold_periodFacts_long | Table | Repository, period, metric and version | Planned |

## 4. Control Layer

### 4.1 Source Registry

Object: eip_vw_control_sourceRegistry_static

Grain: One record per registered source dataset.

Logical Key: sourceId

Deployment: Version-controlled SQL.

| Column | Type | Nullable | Description |
|---|---|---|---|
| sourceId | TEXT | No | Stable source dataset identifier |
| sourceSystem | TEXT | No | External platform name |
| sourceEntity | TEXT | No | Registered source entity |
| sourceDescription | TEXT | No | Description of source contents |
| sourceBaseUrl | TEXT | No | Approved API base URL |
| sourceEndpointTemplate | TEXT | No | Parameterized relative API endpoint |
| httpMethod | TEXT | No | HTTP request method |
| authenticationType | TEXT | No | Authentication mechanism |
| sourceRecordKey | TEXT | No | Identifier attribute in source payload |
| parentSourceId | TEXT | Yes | Logical parent source identifier |
| sourceUpdatedAttribute | TEXT | Yes | Candidate source watermark attribute |
| sourceEventAttribute | TEXT | Yes | Relevant source event timestamp |
| paginationType | TEXT | No | Pagination mechanism |
| extractionStrategy | TEXT | No | Source ingestion strategy |
| targetBronzeTable | TEXT | No | Physical Bronze destination |
| executionSequence | INTEGER | No | Logical source extraction order |
| isActive | INTEGER | No | Source activation indicator |

### 4.2 Registered Source Datasets

| Source ID | Entity | Endpoint |
|---|---|---|
| SRC-001 | Repository | /repos/{owner}/{repo} |
| SRC-002 | Pull Request | /repos/{owner}/{repo}/pulls |
| SRC-003 | Pull Request Detail | /repos/{owner}/{repo}/pulls/{pullRequestNumber} |
| SRC-004 | Pull Request Review | /repos/{owner}/{repo}/pulls/{pullRequestNumber}/reviews |

All endpoints use read-only GET requests.

Authentication credentials are not stored in the registry.

### 4.3 Pipeline Configuration

Object: eip_vw_control_pipelineConfig_static

Grain: One record per configuration parameter.

Logical Key: configKey

| Column | Type | Nullable | Description |
|---|---|---|---|
| configKey | TEXT | No | Stable configuration identifier |
| configCategory | TEXT | No | Functional configuration category |
| configValue | TEXT | No | Default configuration value |
| configDataType | TEXT | No | Declared logical value type |
| configUnit | TEXT | Yes | Unit of measurement |
| configDescription | TEXT | No | Parameter description |
| isActive | INTEGER | No | Configuration activation indicator |

Configuration consumers must convert and validate values
according to their declared logical data types.

### 4.4 Metric Registry

Object: eip_vw_control_metricRegistry_static

Grain: One record per analytical metric.

Logical Key: metricId

| Column | Type | Nullable | Description |
|---|---|---|---|
| metricId | TEXT | No | Stable analytical identifier |
| metricName | TEXT | No | Human-readable metric name |
| metricCategory | TEXT | No | Analytical subject area |
| metricDescription | TEXT | No | Business meaning |
| calculationDefinition | TEXT | No | Deterministic calculation semantics |
| metricUnit | TEXT | No | Measurement unit |
| aggregationType | TEXT | No | Statistical aggregation method |
| analyticalCohort | TEXT | No | Eligible analytical population |
| periodEventAttribute | TEXT | No | Timestamp assigning records to periods |
| sourceDependencies | TEXT | No | Required source identifiers |
| requiresDetailEnrichment | INTEGER | No | PR detail extraction requirement |
| requiresReviewEnrichment | INTEGER | No | Complete review extraction requirement |
| performanceDirection | TEXT | No | Metric interpretation direction |
| supportsHistoricalBenchmark | INTEGER | No | Initial benchmark eligibility |
| interpretationGuidance | TEXT | No | Context and analytical limitations |
| metricVersion | TEXT | No | Semantic definition version |
| displaySequence | INTEGER | No | Presentation order |
| isActive | INTEGER | No | Metric activation indicator |

SQLite views do not enforce logical key uniqueness
or nullability. Automated validation must enforce
these metadata contracts.

### 4.5 Operational Control Tables

The following contracts are proposed.

#### Ingestion Run History

Object: eip_tbl_control_ingestionRunHistory_log

Grain: One record per ingestion execution.

| Column | Proposed Type | Description |
|---|---|---|
| ingestionRunId | TEXT | Unique execution identifier |
| repositoryId | INTEGER | Repository identifier, when resolved |
| repositoryFullName | TEXT | Configured repository name |
| runType | TEXT | INITIAL or INCREMENTAL |
| startedAt | TEXT | Execution start timestamp |
| completedAt | TEXT | Execution completion timestamp |
| runStatus | TEXT | Execution outcome |
| apiRequestsExecuted | INTEGER | Actual upstream requests attempted |
| recordsRetrieved | INTEGER | Total source observations retrieved |
| recordsQuarantined | INTEGER | Invalid observations excluded |
| coverageStatus | TEXT | Observed extraction coverage |
| errorMessage | TEXT | Sanitized execution failure description |

#### Synchronization State

Object: eip_tbl_control_syncState_current

Grain: One record per repository and source dataset.

| Column | Proposed Type | Description |
|---|---|---|
| repositoryId | INTEGER | Repository identifier |
| sourceId | TEXT | Registered source identifier |
| lastSuccessfulRunId | TEXT | Most recent successful source execution |
| lastSuccessfulSyncAt | TEXT | Most recent successful synchronization |
| sourceWatermarkAt | TEXT | Latest safely processed source watermark |
| coverageStartAt | TEXT | Earliest target boundary assessed |
| coverageEndAt | TEXT | Latest reporting coverage boundary assessed |
| coverageStatus | TEXT | Estimated source coverage classification |

A watermark must not advance beyond successfully
processed source coverage.

#### Data Quality Results

Object: eip_tbl_control_dataQualityResults_log

Grain: One recorded validation result.

| Column | Proposed Type | Description |
|---|---|---|
| validationResultId | INTEGER | Unique validation result identifier |
| ingestionRunId | TEXT | Parent ingestion execution |
| repositoryId | INTEGER | Repository identifier |
| sourceId | TEXT | Registered source identifier |
| sourceRecordId | INTEGER | Affected source record, when applicable |
| ruleId | TEXT | Stable validation rule identifier |
| ruleName | TEXT | Human-readable validation rule |
| severity | TEXT | WARNING or ERROR |
| validationStatus | TEXT | Validation outcome |
| validationMessage | TEXT | Sanitized validation failure details |
| validatedAt | TEXT | Validation timestamp |

## 5. Bronze Layer

### 5.1 Purpose

Preserve original source observations before
standardization and analytical transformation.

Bronze records may contain valid or invalid source data.

Raw source observations must never contain authentication
headers, access tokens or environment credentials.

Raw payload content is untrusted and must not be passed
directly into the LLM reasoning context.

### 5.2 Common Bronze Column Contract

The following common columns apply to all four
proposed physical Bronze tables.

| Column | Proposed Type | Nullable | Description |
|---|---|---|---|
| bronzeRecordId | INTEGER | No | Internal unique observation identifier |
| repositoryId | INTEGER | No | Parent GitHub repository identifier |
| sourceRecordId | INTEGER | No | Original GitHub entity identifier |
| rawPayload | TEXT | No | Original source JSON object |
| payloadHash | TEXT | No | SHA-256 fingerprint of serialized payload |
| sourceEndpoint | TEXT | No | Relative source endpoint |
| sourceUpdatedAt | TEXT | Yes | Source update timestamp when available |
| ingestionRunId | TEXT | No | Parent ingestion execution |
| ingestedAt | TEXT | No | UTC observation ingestion timestamp |
| ingestionDate | TEXT | No | UTC ingestion calendar date |

The raw payload preserves source values before
validation or analytical transformation.

Multiple observations of an entity may exist across
different ingestion executions.

### 5.3 Bronze Repository Table

Object: eip_tbl_bronze_githubRepositories_daily

Source: SRC-001

Grain: One repository observation.

sourceRecordId maps to GitHub repository id.

### 5.4 Bronze Pull Request Table

Object: eip_tbl_bronze_githubPullRequests_daily

Source: SRC-002

Grain: One pull request list observation.

sourceRecordId maps to GitHub pull request id.

Additional column:

| Column | Type | Description |
|---|---|---|
| pullRequestNumber | INTEGER | Repository-specific PR number |

### 5.5 Bronze Pull Request Detail Table

Object: eip_tbl_bronze_githubPullRequestDetails_daily

Source: SRC-003

Grain: One pull request detail observation.

sourceRecordId maps to GitHub pull request id.

Additional column:

| Column | Type | Description |
|---|---|---|
| pullRequestNumber | INTEGER | Repository-specific PR number |

### 5.6 Bronze Review Table

Object: eip_tbl_bronze_githubReviews_daily

Source: SRC-004

Grain: One review observation associated with a parent PR.

sourceRecordId maps to GitHub review id.

Additional columns:

| Column | Type | Description |
|---|---|---|
| pullRequestId | INTEGER | Parent GitHub PR identifier |
| pullRequestNumber | INTEGER | Parent repository-specific PR number |

Parent PR identifiers are obtained from extraction context.

## 6. Silver Layer

### 6.1 Purpose

Standardize source attributes, reconcile source observations,
validate identifiers and timestamps, and maintain the latest
valid representation of source entities.

Silver entities use stable business identifiers.

Invalid observations remain in Bronze and are recorded
in operational data quality results.

### 6.2 Repository Source-to-Target Mapping

Object: eip_tbl_silver_repositories_daily

Source: SRC-001

Grain: One repository.

Business Key: repositoryId

| Silver Column | GitHub Attribute | Type | Description |
|---|---|---|---|
| repositoryId | id | INTEGER | Stable repository identifier |
| repositoryName | name | TEXT | Repository name |
| repositoryFullName | full_name | TEXT | Owner-qualified repository name |
| ownerId | owner.id | INTEGER | Repository owner identifier |
| ownerName | owner.login | TEXT | Repository owner account |
| repositoryDescription | description | TEXT | Repository description |
| primaryLanguage | language | TEXT | Primary repository language |
| defaultBranch | default_branch | TEXT | Default source branch |
| createdAt | created_at | TEXT | Repository creation timestamp |
| updatedAt | updated_at | TEXT | Repository update timestamp |
| pushedAt | pushed_at | TEXT | Latest push timestamp |
| starsCount | stargazers_count | INTEGER | Current observed star count |
| forksCount | forks_count | INTEGER | Current observed fork count |
| openIssuesCount | open_issues_count | INTEGER | GitHub open issue count including PRs |
| isArchived | archived | INTEGER | Repository archived indicator |
| isPrivate | private | INTEGER | Repository privacy indicator |
| repositoryUrl | html_url | TEXT | Public-facing repository URL |

### 6.3 Pull Request Source-to-Target Mapping

Object: eip_tbl_silver_pullRequests_daily

Sources: SRC-002, SRC-003

Grain: One pull request per repository.

Business Key: repositoryId, pullRequestId

Alternate Key: repositoryId, pullRequestNumber

#### Basic Pull Request Attributes

| Silver Column | Source Attribute | Type | Description |
|---|---|---|---|
| repositoryId | Extraction context | INTEGER | Parent repository identifier |
| pullRequestId | id | INTEGER | Stable GitHub PR identifier |
| pullRequestNumber | number | INTEGER | Repository-specific PR number |
| pullRequestState | state | TEXT | Current observed PR state |
| isDraft | draft | INTEGER | Current observed draft indicator |
| authorId | user.id | INTEGER | PR author identifier |
| authorName | user.login | TEXT | PR author account |
| authorType | user.type | TEXT | GitHub author account type |
| authorAssociation | author_association | TEXT | Author relationship to repository |
| createdAt | created_at | TEXT | PR creation timestamp |
| updatedAt | updated_at | TEXT | Latest observed update timestamp |
| closedAt | closed_at | TEXT | Observed closure timestamp |
| mergedAt | merged_at | TEXT | Successful merge timestamp |
| targetBranch | base.ref | TEXT | PR destination branch |
| sourceBranch | head.ref | TEXT | PR source branch |
| pullRequestUrl | html_url | TEXT | Public-facing PR URL |

#### PR Detail Attributes

| Silver Column | Source Attribute | Type | Description |
|---|---|---|---|
| isMerged | merged or mergedAt | INTEGER | Successful merge indicator |
| additionsCount | additions | INTEGER | Added code lines |
| deletionsCount | deletions | INTEGER | Deleted code lines |
| changedFilesCount | changed_files | INTEGER | Number of changed files |
| commitsCount | commits | INTEGER | Number of PR commits |
| commentsCount | comments | INTEGER | PR conversation comments |
| reviewCommentsCount | review_comments | INTEGER | Inline review comments |
| mergedById | merged_by.id | INTEGER | Merging account identifier |
| mergedByName | merged_by.login | TEXT | Merging account name |

isMerged can be derived from a valid non-null mergedAt
when detail enrichment is unavailable.

The reviewCommentsCount attribute does not represent
the number of submitted PR review records.

Uncollected detail statistics remain NULL.

#### Enrichment Completeness Attributes

| Silver Column | Type | Description |
|---|---|---|
| isDetailExtractionComplete | INTEGER | Valid detail extraction completed |
| isReviewExtractionComplete | INTEGER | All review pages retrieved and reconciled |
| detailExtractedAt | TEXT | Latest successful detail extraction |
| reviewExtractedAt | TEXT | Latest complete review extraction |

Completeness must be invalidated or reassessed when
a parent source observation changes and previously
collected enrichment may no longer be current.

### 6.4 Review Source-to-Target Mapping

Object: eip_tbl_silver_reviews_daily

Source: SRC-004

Grain: One review per pull request.

Business Key: repositoryId, pullRequestId, reviewId

| Silver Column | Source Attribute | Type | Description |
|---|---|---|---|
| repositoryId | Extraction context | INTEGER | Parent repository identifier |
| pullRequestId | Extraction context | INTEGER | Parent PR identifier |
| pullRequestNumber | Extraction context | INTEGER | Repository-specific PR number |
| reviewId | id | INTEGER | Stable GitHub review identifier |
| reviewerId | user.id | INTEGER | Reviewer account identifier |
| reviewerName | user.login | TEXT | Reviewer account name |
| reviewerType | user.type | TEXT | Reviewer account type |
| reviewState | state | TEXT | Observed review state |
| submittedAt | submitted_at | TEXT | Review submission timestamp |
| reviewerAssociation | author_association | TEXT | Reviewer relationship to repository |
| reviewedCommitId | commit_id | TEXT | Reviewed commit identifier |
| reviewUrl | html_url | TEXT | Public-facing review URL |

Unknown reviewer information and unsubmitted reviews
must be represented accurately rather than fabricated.

### 6.5 Silver Operational Metadata

The following metadata is proposed for Silver entities.

| Column | Type | Description |
|---|---|---|
| ingestionRunId | TEXT | Run producing the latest valid entity |
| bronzeRecordId | INTEGER | Latest contributing basic source observation |
| processedAt | TEXT | Latest successful transformation timestamp |

PR detail lineage must also be retained separately
from the basic PR observation lineage.

## 7. Gold Layer

### 7.1 Purpose

Provide deterministic analytical facts for the insights API,
dashboard and AI reasoning engine.

All Gold calculations must use validated source entities
and explicit analytical cohort definitions.

### 7.2 PR Lifecycle Facts

Object: eip_tbl_gold_prLifecycle_wide

Grain: One pull request per repository.

Business Key: repositoryId, pullRequestId

| Column | Proposed Type | Description |
|---|---|---|
| repositoryId | INTEGER | Parent repository identifier |
| pullRequestId | INTEGER | Stable PR identifier |
| pullRequestNumber | INTEGER | Repository-specific PR number |
| authorId | INTEGER | PR author identifier |
| pullRequestState | TEXT | Current observed PR state |
| isDraft | INTEGER | Current observed draft indicator |
| isMerged | INTEGER | Successful merge indicator |
| createdAt | TEXT | PR creation timestamp |
| closedAt | TEXT | Observed closure timestamp |
| mergedAt | TEXT | Successful merge timestamp |
| firstReviewAt | TEXT | Earliest qualifying external review |
| lastReviewAt | TEXT | Latest qualifying external review |
| externalReviewCount | INTEGER | Qualifying external review records |
| uniqueExternalReviewerCount | INTEGER | Distinct qualifying reviewer accounts |
| linesChanged | INTEGER | Additions plus deletions |
| changedFilesCount | INTEGER | Number of changed files |
| mergeHours | REAL | Creation-to-merge elapsed hours |
| preReviewHours | REAL | Creation-to-first-review elapsed hours |
| postReviewHours | REAL | First-review-to-merge elapsed hours |
| preReviewTimeSharePct | REAL | Pre-review share of merge duration |
| isDetailExtractionComplete | INTEGER | Detail source completeness |
| isReviewExtractionComplete | INTEGER | Review source completeness |
| ingestionRunId | TEXT | Relevant processing execution |
| calculatedAt | TEXT | Analytical calculation timestamp |

Review counts remain NULL when review extraction
is incomplete.

A zero externalReviewCount is valid only after
complete review extraction and qualification.

### 7.3 Period Analytical Facts

Object: eip_tbl_gold_periodFacts_long

Grain: One metric per repository, reporting period,
period type and metric version.

| Column | Proposed Type | Description |
|---|---|---|
| repositoryId | INTEGER | Repository identifier |
| periodType | TEXT | Reporting period classification |
| periodStart | TEXT | Inclusive UTC reporting start |
| periodEndExclusive | TEXT | Exclusive UTC reporting end |
| metricId | TEXT | Registered metric identifier |
| metricVersion | TEXT | Metric definition version |
| metricUnit | TEXT | Measurement unit |
| currentValue | REAL | Deterministically calculated metric |
| previousValue | REAL | Previous comparable period value |
| changeValue | REAL | Absolute change from previous period |
| changePct | REAL | Relative percentage change |
| historical4PeriodAvg | REAL | Mean of four prior period values |
| historical4PeriodStd | REAL | Sample standard deviation of prior values |
| changeVsBenchmarkPct | REAL | Relative deviation from benchmark |
| benchmarkPeriodCount | INTEGER | Eligible historical periods |
| eligiblePRCount | INTEGER | Observed PRs eligible for metric assessment |
| enrichedPRCount | INTEGER | Eligible PRs with required source enrichment |
| sampleSize | INTEGER | PRs contributing valid metric observations |
| enrichmentCoveragePct | REAL | Required enrichment completeness |
| coverageStatus | TEXT | Source and analytical coverage classification |
| evidenceId | TEXT | Stable analytical evidence identifier |
| ingestionRunId | TEXT | Relevant processing execution |
| calculatedAt | TEXT | Analytical calculation timestamp |

The full business key includes repositoryId, periodType,
periodStart, periodEndExclusive, metricId and metricVersion.

For metrics that require no additional source enrichment,
enrichment coverage may be represented as not applicable.

Historical benchmark values remain NULL when insufficient
comparable periods are available.

Percentage changes remain NULL when the comparison
denominator is zero or unavailable.

## 8. Analytical Data Quality Rules

| Rule | Requirement |
|---|---|
| Identifier integrity | Stable source identifiers must be valid |
| Entity uniqueness | Silver business keys must be unique |
| Referential integrity | Reviews must reference valid parent PRs |
| Creation integrity | PR creation timestamps must be populated |
| Update integrity | Update timestamps cannot precede creation |
| Closure integrity | Closure timestamps cannot precede creation |
| Merge integrity | Merge timestamps cannot precede creation |
| Review integrity | Qualifying reviews must occur within eligible lifecycle boundaries |
| Count integrity | Code change and activity counts cannot be negative |
| Lifecycle reconciliation | Merge duration equals pre-review plus post-review duration for the same reviewed merged PR |
| Coverage integrity | Missing enrichment cannot be represented as observed zero activity |

## 9. Review Qualification Policy

A qualifying external review must satisfy:

- Known PR author and reviewer identifiers.
- Reviewer identifier differs from PR author identifier.
- Reviewer account type equals User.
- Submitted review state is APPROVED,
  CHANGES_REQUESTED, COMMENTED or DISMISSED.
- Submission timestamp is on or after PR creation.
- For merged PRs, submission occurs on or before merge.

Dismissed reviews represent historical participation,
not currently valid approval.

GitHub account type User does not conclusively establish
that an account is operated by a human.

## 10. Source Coverage and Analytical Limitations

Initial target coverage:

- Basic PR ingestion: 60 days.
- Merged cohort detail and review enrichment: 14 days.
- Default reporting period: seven complete UTC days.
- Historical benchmark: four preceding periods.

These are configurable planning defaults.

Boundary confirmation does not guarantee exhaustive
source coverage.

Source-level coverage and enrichment-level coverage
must be tracked independently.

All durations represent elapsed calendar time rather
than active engineering effort.

## 11. Data Governance

- Authentication credentials remain outside database payloads.
- Source inputs are treated as untrusted.
- Raw source text is excluded from LLM reasoning context.
- SQL data values are parameterized.
- Repository and endpoint parameters are validated.
- Data quality failures retain source lineage.
- Historical metrics disclose source limitations.
- Metric definitions are version-controlled.
- Database files remain excluded from Git.
- Raw source retention must remain bounded.

## 12. Implementation Status

| Component | Status |
|---|---|
| Source Registry | Validated |
| Pipeline Configuration | Validated |
| Metric Registry | Validated |
| Physical Control Tables | Planned |
| Physical Bronze Tables | Planned |
| Silver Transformations | Planned |
| Gold Calculations | Planned |
| Production API Client | Planned |
| AI Evidence Validation | Planned |

Proposed physical column definitions will be reconciled
against implemented SQL schemas during development.
