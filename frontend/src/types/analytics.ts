export type MetricUnit =
  | 'COUNT'
  | 'HOURS'
  | 'PERCENT'
  | 'LINES'
  | 'FILES'

export type MetricCategory =
  | 'LIFECYCLE'
  | 'COLLABORATION'
  | 'CODE_CHANGE'

export type PerformanceDirection =
  | 'HIGHER_IS_BETTER'
  | 'LOWER_IS_BETTER'
  | 'CONTEXT_DEPENDENT'

export interface ReportingPeriod {
  periodStart: string
  periodEndExclusive: string
}

export interface AvailableHistory {
  start: string
  endExclusive: string
  enrichmentStart: string | null
}

export interface AnalyticalMetric {
  repositoryId: number

  periodType: string
  periodStart: string
  periodEndExclusive: string

  metricId: string
  metricVersion: string
  metricUnit: MetricUnit

  // Analytical values

  currentValue: number | null
  previousValue: number | null
  changeValue: number | null
  changePct: number | null

  // Historical benchmarks

  historicalBenchmarkAvg: number | null
  historicalBenchmarkStd: number | null
  changeVsBenchmarkPct: number | null
  benchmarkPeriodCount: number

  // Data quality and coverage

  eligiblePRCount: number | null
  enrichedPRCount: number | null
  sampleSize: number | null
  enrichmentCoveragePct: number | null
  coverageStatus: string

  previousSampleSize: number | null
  previousEnrichmentCoveragePct: number | null
  previousCoverageStatus: string | null

  // Evidence and lineage

  evidenceId: string
  ingestionRunId: string
  calculatedAt: string

  // Semantic metadata

  metricName: string
  metricCategory: MetricCategory
  metricDescription: string
  calculationDefinition: string
  analyticalCohort: string
  aggregationType: string
  periodEventAttribute: string
  sourceDependencies: string

  requiresDetailEnrichment: 0 | 1
  requiresReviewEnrichment: 0 | 1

  performanceDirection: PerformanceDirection

  supportsHistoricalBenchmark: 0 | 1
  interpretationGuidance: string
}

export interface InsightsResponse {
  repository: string
  repositoryId: number
  ingestionRunId: string

  periodStart: string
  periodEndExclusive: string

  previousPeriodStart: string
  previousPeriodEndExclusive: string

  reportingTimezone: string
  sourceCoverage: string
  dataRefreshedAt: string

  availableHistory: AvailableHistory

  metricCount: number
  metrics: AnalyticalMetric[]
}
