export interface AssessmentCriterion {
  key: string
  label: string
  weight: number
  description: string
}

export const evaluationCriteria: AssessmentCriterion[] = [
  {
    key: 'factualConsistency',
    label: 'Factual Consistency',
    weight: 30,
    description: 'Agreement with the underlying analytical facts.',
  },
  {
    key: 'evidenceGrounding',
    label: 'Evidence Grounding',
    weight: 25,
    description: 'Claims supported by relevant evidence references.',
  },
  {
    key: 'analyticalReasoning',
    label: 'Analytical Reasoning',
    weight: 20,
    description: 'Logical interpretation of metric relationships.',
  },
  {
    key: 'counterEvidence',
    label: 'Counter-Evidence',
    weight: 10,
    description: 'Consideration of evidence challenging the hypothesis.',
  },
  {
    key: 'uncertaintyHandling',
    label: 'Uncertainty Handling',
    weight: 10,
    description: 'Distinction between facts and potential explanations.',
  },
  {
    key: 'businessRelevance',
    label: 'Business Relevance',
    weight: 5,
    description: 'Usefulness for engineering decisions.',
  },
]

export const confidenceCriteria: AssessmentCriterion[] = [
  {
    key: 'dataCoverage',
    label: 'Data Coverage',
    weight: 25,
    description: 'Availability and completeness of cited analytical data.',
  },
  {
    key: 'sampleAdequacy',
    label: 'Sample Adequacy',
    weight: 20,
    description: 'Sufficiency of observations supporting the analysis.',
  },
  {
    key: 'supportingEvidence',
    label: 'Supporting Evidence',
    weight: 25,
    description: 'Breadth of evidence supporting the conclusions.',
  },
  {
    key: 'counterEvidence',
    label: 'Counter-Evidence',
    weight: 15,
    description: 'Evidence cited that challenges the hypothesis.',
  },
  {
    key: 'historicalConsistency',
    label: 'Historical Consistency',
    weight: 15,
    description: 'Support from available historical benchmarks.',
  },
]

export function calculateWeightedScore(
  scores: Record<string, number>,
  criteria: AssessmentCriterion[],
): number | null {
  if (criteria.some(item => !Number.isFinite(scores[item.key]))) {
    return null
  }

  return criteria.reduce(
    (total, item) =>
      total + scores[item.key] * item.weight / 100,
    0,
  )
}
