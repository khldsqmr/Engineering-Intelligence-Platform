import { apiRequest } from './apiClient'

import type { ReportingPeriod } from '../types/analytics'
import type { NarrativeResponse } from '../types/intelligence'

export interface CopilotResponse
  extends Omit<NarrativeResponse, 'status'> {
  question: string
  conversationContextVersion?: string
  status:
    | NarrativeResponse['status']
    | 'INSUFFICIENT_EVIDENCE'
    | 'FACT_ANSWERED'
    | 'CHAT_ANSWERED'
  chatAnswer?: string
  intentRouterVersion?: string
  intentPlannerVersion?: string
  plannerStatus?: 'VALIDATED' | 'UNRESOLVED'
  factAnswer?: string
  factFallback?: string
  factAnswerVersion?: string
}

export function askCopilot(
  question: string,
  period: ReportingPeriod,
  previousQuestions: string[] = [],
) {
  return apiRequest<CopilotResponse>(
    '/api/v1/ai/copilot',
    {
      method: 'POST',
      body: JSON.stringify({
        question: question.trim(),
        previousQuestions,
        periodStart: period.periodStart,
        periodEndExclusive: period.periodEndExclusive,
      }),
    },
  )
}
