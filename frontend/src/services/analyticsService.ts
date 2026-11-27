import { apiRequest } from './apiClient'

import type {
  InsightsResponse,
  ReportingPeriod,
} from '../types/analytics'

export function getInsights(
  period?: ReportingPeriod,
  signal?: AbortSignal,
): Promise<InsightsResponse> {
  const params = new URLSearchParams()

  if (period) {
    params.set('periodStart', period.periodStart)

    params.set(
      'periodEndExclusive',
      period.periodEndExclusive,
    )
  }

  const query = params.toString()

  const path = query
    ? `/api/v1/insights?${query}`
    : '/api/v1/insights'

  return apiRequest<InsightsResponse>(path, {
    signal,
  })
}
