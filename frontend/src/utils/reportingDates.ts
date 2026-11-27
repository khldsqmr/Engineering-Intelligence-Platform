import type { ReportingPeriod } from '../types/analytics'

export function shiftDate(
  date: string,
  days: number,
): string {
  const result = new Date(date)

  result.setUTCDate(result.getUTCDate() + days)

  return result.toISOString().slice(0, 10)
}

export function shiftReportingWeek(
  period: ReportingPeriod,
  weeksBack: number,
): ReportingPeriod {
  return {
    periodStart: shiftDate(
      period.periodStart,
      -7 * weeksBack,
    ),

    periodEndExclusive: shiftDate(
      period.periodEndExclusive,
      -7 * weeksBack,
    ),
  }
}

export function getWeekDates(
  periodStart: string,
): string[] {
  return Array.from(
    { length: 7 },
    (_, index) => shiftDate(periodStart, index),
  )
}

export function formatReportingDate(
  date: string,
): string {
  return new Intl.DateTimeFormat('en-CA', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    timeZone: 'UTC',
  }).format(new Date(date))
}

export function formatReportingPeriod(
  period: ReportingPeriod,
): string {
  return [
    formatReportingDate(period.periodStart),
    formatReportingDate(
      shiftDate(period.periodEndExclusive, -1),
    ),
  ].join(' – ')
}
