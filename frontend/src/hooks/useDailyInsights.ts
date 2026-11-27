import { useQueries } from '@tanstack/react-query'

import { getInsights } from '../services/analyticsService'

import type {
  AvailableHistory,
  InsightsResponse,
  ReportingPeriod,
} from '../types/analytics'

import {
  getWeekDates,
  shiftDate,
} from '../utils/reportingDates'

export type DailyDataState =
  | 'ACTUAL'
  | 'LOADING'
  | 'NOT_AVAILABLE'
  | 'PENDING'
  | 'ERROR'

export interface DailyInsight {
  date: string
  state: DailyDataState
  data: InsightsResponse | undefined
}

export function useDailyInsights(
  period?: ReportingPeriod,
  history?: AvailableHistory,
) {
  const dates = period
    ? getWeekDates(period.periodStart)
    : []

  const historyStart =
    history?.start.slice(0, 10)

  const historyEnd =
    history?.endExclusive.slice(0, 10)

  const queries = useQueries({
    queries: dates.map(date => {
      const end = shiftDate(date, 1)

      const enabled = Boolean(
        historyStart &&
        historyEnd &&
        date >= historyStart &&
        end <= historyEnd,
      )

      return {
        queryKey: ['insights', date, end],

        queryFn: ({ signal }: { signal: AbortSignal }) =>
          getInsights(
            {
              periodStart: date,
              periodEndExclusive: end,
            },
            signal,
          ),

        enabled,
      }
    }),
  })

  const days: DailyInsight[] = dates.map(
    (date, index) => {
      const query = queries[index]

      let state: DailyDataState

      if (!historyStart || !historyEnd) {
        state = 'NOT_AVAILABLE'
      } else if (date >= historyEnd) {
        state = 'PENDING'
      } else if (date < historyStart) {
        state = 'NOT_AVAILABLE'
      } else if (query?.isError) {
        state = 'ERROR'
      } else if (query?.data) {
        state = 'ACTUAL'
      } else {
        state = 'LOADING'
      }

      return {
        date,
        state,
        data: state === 'ACTUAL'
          ? query?.data
          : undefined,
      }
    },
  )

  return {
    days,

    isLoading: days.some(
      day => day.state === 'LOADING',
    ),

    hasErrors: days.some(
      day => day.state === 'ERROR',
    ),

    retryFailed: () => {
      queries.forEach(query => {
        if (query.isError) {
          void query.refetch()
        }
      })
    },
  }
}
