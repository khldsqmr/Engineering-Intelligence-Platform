import { useQuery } from '@tanstack/react-query'

import { getInsights } from '../services/analyticsService'

import type {
  ReportingPeriod,
} from '../types/analytics'

export function useInsights(
  period?: ReportingPeriod,
) {
  return useQuery({
    queryKey: [
      'insights',
      period?.periodStart ?? 'latest',
      period?.periodEndExclusive ?? 'latest',
    ],

    queryFn: ({ signal }) =>
      getInsights(period, signal),
  })
}
