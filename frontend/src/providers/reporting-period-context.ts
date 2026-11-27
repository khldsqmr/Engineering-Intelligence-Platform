import { createContext, useContext } from 'react'

interface ReportingPeriodContextValue {
  weeksBack: number
  setWeeksBack: (value: number) => void
}

export const ReportingPeriodContext =
  createContext<ReportingPeriodContextValue | undefined>(
    undefined,
  )

export function useReportingPeriod() {
  const context = useContext(ReportingPeriodContext)

  if (!context) {
    throw new Error(
      'ReportingPeriodProvider is required',
    )
  }

  return context
}
