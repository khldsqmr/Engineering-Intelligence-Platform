import { useState } from 'react'
import type { ReactNode } from 'react'

import {
  ReportingPeriodContext,
} from './reporting-period-context'

export function ReportingPeriodProvider({
  children,
}: {
  children: ReactNode
}) {
  const [weeksBack, setWeeksBack] = useState(0)

  return (
    <ReportingPeriodContext.Provider
      value={{ weeksBack, setWeeksBack }}
    >
      {children}
    </ReportingPeriodContext.Provider>
  )
}
