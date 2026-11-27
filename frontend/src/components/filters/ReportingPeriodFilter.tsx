import {
  CalendarDays,
  ChevronLeft,
  ChevronRight,
  GitBranch,
  RotateCcw,
} from 'lucide-react'

import type {
  useReportingWeek,
} from '../../hooks/useReportingWeek'

import {
  formatReportingPeriod,
} from '../../utils/reportingDates'

interface ReportingPeriodFilterProps {
  week: ReturnType<typeof useReportingWeek>
}

export function ReportingPeriodFilter({
  week,
}: ReportingPeriodFilterProps) {
  if (!week.latestData || !week.period) {
    return null
  }

  return (
    <div className="reporting-filter">

      <div className="reporting-repository">
        <GitBranch size={18} />

        <div>
          <span className="filter-label">
            Repository
          </span>

          <strong>
            {week.latestData.repository}
          </strong>
        </div>
      </div>

      <div className="reporting-date-controls">

        <button
          className="icon-button"
          aria-label="Previous reporting week"
          disabled={!week.canGoPrevious}
          onClick={week.previousWeek}
        >
          <ChevronLeft size={18} />
        </button>

        <div className="reporting-date">

          <CalendarDays size={17} />

          <div>
            <span className="filter-label">
              Reporting week · UTC
            </span>

            <strong>
              {formatReportingPeriod(week.period)}
            </strong>
          </div>

        </div>

        <button
          className="icon-button"
          aria-label="Next reporting week"
          disabled={!week.canGoNext}
          onClick={week.nextWeek}
        >
          <ChevronRight size={18} />
        </button>

        <button
          className="icon-button"
          aria-label="Return to latest reporting week"
          title="Latest reporting week"
          disabled={!week.canGoNext}
          onClick={week.resetWeek}
        >
          <RotateCcw size={16} />
        </button>

      </div>

    </div>
  )
}
