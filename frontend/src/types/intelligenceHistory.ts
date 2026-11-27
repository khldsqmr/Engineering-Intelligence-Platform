import type { IntelligenceAudit } from './intelligenceAudit'

export interface IntelligenceHistoryRecord {
  intelligenceId: string
  repository: string
  ingestionRunId: string
  periodStart: string
  periodEndExclusive: string
  approvalStatus: string
  evaluationScore: number | null
  confidenceScore: number | null
  deterministicValidationPassed: number
  eligibleForHistoricalContext: number
  generatorModel: string
  evaluatorModel: string | null
  generationLatencySeconds: number | null
  evaluatorLatencySeconds: number | null
  createdAt: string
}

export interface IntelligenceHistoryResponse {
  repository: string
  total: number
  limit: number
  offset: number
  records: IntelligenceHistoryRecord[]
}

export interface IntelligenceHistoryDetail extends IntelligenceAudit {
  repository: string
  ingestionRunId: string
  periodStart: string
  periodEndExclusive: string
  contextVersion: string
  context: unknown
  modelInput: unknown
  response: unknown
  narrative: string | null
  hypothesis: string | null
  metricVersions: Record<string, string>
}
