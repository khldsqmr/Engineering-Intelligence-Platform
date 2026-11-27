export interface IntelligenceAudit {
  intelligenceId: string
  auditOnly: boolean
  approvalStatus: string

  generatorModel: string
  generatorPromptVersion: string
  generationLatencySeconds: number | null
  generationInputTokens: number | null
  generationOutputTokens: number | null

  evaluatorModel: string | null
  evaluatorPromptVersion: string | null
  evaluatorLatencySeconds: number | null

  evaluationVersion: string
  evaluationScore: number | null

  deterministicValidationPassed: number
  eligibleForHistoricalContext: number
  historicalIntelligenceIds: string[]

  evaluation: {
    evaluationVersion: string
    deterministicValidationPassed: boolean
    findings: unknown[]
    judgeResult: {
      scores: Record<string, number>
      criticalErrors: unknown[]
      explanation: string
    } | null
  } | null

  confidenceVersion: string
  confidenceScore: number | null

  confidence: {
    confidenceVersion: string
    confidenceScore: number
    dimensions: Record<string, number>
    appliedCap: number | null
    limitations: string[]
  } | null

  createdAt: string
}
