import {
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query'

import {
  getNarrative,
  generateNarrative,
} from '../services/intelligenceService'

import type {
  InsightsResponse,
  ReportingPeriod,
} from '../types/analytics'

export function useNarrative(analytics: InsightsResponse) {
  const queryClient = useQueryClient()

  const period: ReportingPeriod = {
    periodStart: analytics.periodStart,
    periodEndExclusive: analytics.periodEndExclusive,
  }

  const queryKey = [
    'narrative',
    analytics.repository,
    analytics.ingestionRunId,
    period.periodStart,
    period.periodEndExclusive,
  ]

  const query = useQuery({
    queryKey,
    queryFn: ({ signal }) => getNarrative(period, signal),
  })

  const generation = useMutation({
    mutationFn: () => generateNarrative(period),
    retry: false,

    onMutate: async () => {
      await queryClient.cancelQueries({
        queryKey,
        exact: true,
      })
    },

    onSuccess: result => {
      queryClient.setQueryData(queryKey, result)
    },
  })

  return {
    query,
    generation,
  }
}
