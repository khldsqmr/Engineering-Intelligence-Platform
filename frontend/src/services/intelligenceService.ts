import type {
  IntelligenceHistoryResponse,
  IntelligenceHistoryDetail,
} from '../types/intelligenceHistory'

import type { IntelligenceContext } from '../types/context'
import type { IntelligenceAudit } from '../types/intelligenceAudit'
import { apiRequest } from './apiClient'

import type { ReportingPeriod } from '../types/analytics'
import type { NarrativeResponse } from '../types/intelligence'

export function getNarrative(
  period: ReportingPeriod,
  signal?: AbortSignal,
) {
  const parameters = new URLSearchParams({
    periodStart: period.periodStart,
    periodEndExclusive: period.periodEndExclusive,
  })

  return apiRequest<NarrativeResponse>(
    `/api/v1/ai/narrative?${parameters}`,
    { signal },
  )
}

export function generateNarrative(period: ReportingPeriod) {
  return apiRequest<NarrativeResponse>(
    '/api/v1/ai/narrative',
    {
      method: 'POST',
      body: JSON.stringify({
        periodStart: period.periodStart,
        periodEndExclusive: period.periodEndExclusive,
        forceRefresh: false,
      }),
    },
  )
}


export function getIntelligenceAudit(
  intelligenceId: string,
  signal?: AbortSignal,
) {
  return apiRequest<IntelligenceAudit>(
    `/api/v1/ai/history/${encodeURIComponent(intelligenceId)}`,
    { signal },
  )
}


export function getIntelligenceContext(
  period: ReportingPeriod,
  signal?: AbortSignal,
) {
  const parameters = new URLSearchParams({
    periodStart: period.periodStart,
    periodEndExclusive: period.periodEndExclusive,
  })

  return apiRequest<IntelligenceContext>(
    `/api/v1/ai/context?${parameters}`,
    { signal },
  )
}


export function getIntelligenceHistory(
  limit = 10,
  offset = 0,
  signal?: AbortSignal,
) {
  const parameters = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
    mode: 'all',
  })

  return apiRequest<IntelligenceHistoryResponse>(
    `/api/v1/ai/history?${parameters}`,
    { signal },
  )
}

export function getIntelligenceHistoryDetail(
  intelligenceId: string,
  signal?: AbortSignal,
) {
  return apiRequest<IntelligenceHistoryDetail>(
    `/api/v1/ai/history/${encodeURIComponent(intelligenceId)}`,
    { signal },
  )
}
