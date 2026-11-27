import { useInsights } from './useInsights'

import {
  useReportingPeriod,
} from '../providers/reporting-period-context'

import {
  shiftReportingWeek,
} from '../utils/reportingDates'

const WEEK_MS = 7 * 24 * 60 * 60 * 1000

export function useReportingWeek() {
  const latest = useInsights()

  const {
    weeksBack,
    setWeeksBack,
  } = useReportingPeriod()

  const latestData = latest.data

  const maxWeeksBack = latestData
    ? Math.max(
        0,
        Math.floor(
          (
            Date.parse(latestData.periodStart)
            - Date.parse(
                latestData.availableHistory.start,
              )
          ) / WEEK_MS,
        ),
      )
    : 0

  const selectedWeeksBack = Math.min(
    Math.max(weeksBack, 0),
    maxWeeksBack,
  )

  const period = latestData
    ? shiftReportingWeek(
        latestData,
        selectedWeeksBack,
      )
    : undefined

  const query = useInsights(
    selectedWeeksBack === 0
      ? undefined
      : period,
  )

  return {
    query,
    period,
    latestData,

    weeksBack: selectedWeeksBack,

    canGoPrevious:
      selectedWeeksBack < maxWeeksBack,

    canGoNext:
      selectedWeeksBack > 0,

    previousWeek: () =>
      setWeeksBack(
        Math.min(
          selectedWeeksBack + 1,
          maxWeeksBack,
        ),
      ),

    nextWeek: () =>
      setWeeksBack(
        Math.max(selectedWeeksBack - 1, 0),
      ),

    resetWeek: () => setWeeksBack(0),
  }
}
