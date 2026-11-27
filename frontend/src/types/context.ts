export interface TemporalContext {
  periodStart: string
  periodEndExclusive: string
  previousPeriodStart: string
  previousPeriodEndExclusive: string
  timezone: string
}

export interface SemanticContext {
  metricId: string
  metricVersion: string
  metricName: string
  metricCategory: string
  metricDescription: string
  metricUnit: string
  calculationDefinition: string
  analyticalCohort: string
  aggregationType: string
  periodEventAttribute: string
  sourceDependencies: string
  requiresDetailEnrichment: boolean
  requiresReviewEnrichment: boolean
  performanceDirection: string
  supportsHistoricalBenchmark: boolean
  interpretationGuidance: string
}

export interface AnalyticalContext {
  evidenceRef: string
  evidenceId: string
  metricId: string
  metricVersion: string
  currentValue: number | null
  previousValue: number | null
  changeValue: number | null
  changePct: number | null
  direction: string
  historicalBenchmarkAvg: number | null
  historicalBenchmarkStd: number | null
  changeVsBenchmarkPct: number | null
  benchmarkPeriodCount: number
  eligiblePRCount: number | null
  enrichedPRCount: number | null
  sampleSize: number | null
  enrichmentCoveragePct: number | null
  coverageStatus: string
  previousSampleSize: number | null
  previousEnrichmentCoveragePct: number | null
  previousCoverageStatus: string | null
}

export interface RelationalContext {
  relationshipId: string
  relationshipType: string
  metricIds: string[]
  interpretation: string
}

export interface HistoricalContext {
  intelligenceId: string
  periodStart: string
  periodEndExclusive: string
  narrative: string
  metricVersions: Record<string, string>
  evaluationScore: number
  evaluationVersion: string
}

export interface IntelligenceContext {
  contextVersion: string
  repository: string
  repositoryId: number
  ingestionRunId: string
  temporalContext: TemporalContext
  semanticContext: SemanticContext[]
  analyticalContext: AnalyticalContext[]
  relationalContext: RelationalContext[]
  historicalContext: HistoricalContext[]

  qualityContext: {
    sourceCoverage: string
    dataRefreshedAt: string
    availableHistory: Record<string, string | null>
    limitations: string[]
  }

  userIntent: {
    mode: string
    question: string | null
  }
}
