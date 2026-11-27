export interface EvidenceReference {
  evidenceRef: string
  direction: string
}

export interface AnalyticalClaim {
  text: string
  supportingEvidence: EvidenceReference[]
}

export interface RootCauseHypothesis extends AnalyticalClaim {
  counterEvidence: EvidenceReference[]
}

export interface NarrativeOutput {
  status: 'ANSWERED' | 'INSUFFICIENT_EVIDENCE'
  narrative: AnalyticalClaim | null
  hypothesis: RootCauseHypothesis | null
  alternativeExplanations: string[]
  recommendedInvestigation: string | null
}

export interface IntelligenceEvidence {
  evidenceRef: string
  evidenceId: string
  metricId: string
  metricVersion: string
  currentValue: number | null
  previousValue: number | null
  changeValue: number | null
  changePct: number | null
  sampleSize: number | null
  coverageStatus: string
  direction: string

  semanticContext: {
    metricName: string
    metricUnit: string
    metricDescription: string
    calculationDefinition: string
  }
}

export type IntelligenceStatus =
  | 'AUTO_APPROVED'
  | 'NOT_GENERATED'
  | 'REGENERATE'
  | 'REJECTED'
  | 'EVALUATION_FAILED'

export interface NarrativeResponse {
  evaluatorModel?: string | null
  repository: string
  periodStart: string
  periodEndExclusive: string
  status: IntelligenceStatus
  intelligenceId: string | null
  cacheHit: boolean
  evaluationScore: number | null
  confidenceScore: number | null
  response: NarrativeOutput | null
  evidence: IntelligenceEvidence[]
}
