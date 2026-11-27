import { useState } from 'react'
import {
  Activity,
  ChevronDown,
  ChevronUp,
} from 'lucide-react'

import { PageHeader } from '../../../components/layout/PageHeader'
import { ReportingPeriodFilter } from '../../../components/filters/ReportingPeriodFilter'
import { MetricTrendChart } from '../../../components/charts/MetricTrendChart'

import { useReportingWeek } from '../../../hooks/useReportingWeek'
import { useDailyInsights } from '../../../hooks/useDailyInsights'

import { WeeklyPerformanceMatrix } from './components/WeeklyPerformanceMatrix'

export function PerformanceManagementPage() {
  const [showTrend, setShowTrend] = useState(false)

  const week = useReportingWeek()

  const {
    data,
    isPending,
    isError,
    refetch,
  } = week.query

  const daily = useDailyInsights(
    data,
    data?.availableHistory,
  )

  return (
    <section className="workspace-page performance-workspace">

      <PageHeader
        category="Analytics"
        title="Performance Management"
        description="Daily engineering metrics and week-to-date performance."
      />

      <ReportingPeriodFilter week={week} />

      {isPending ? (
        <div className="empty-state" role="status">
          Loading performance metrics...
        </div>
      ) : isError || !data ? (
        <div className="empty-state">
          <h2>Unable to load performance data</h2>

          <button
            type="button"
            className="primary-button"
            onClick={() => void refetch()}
          >
            Retry
          </button>
        </div>
      ) : (
        <>
          <WeeklyPerformanceMatrix
            key={data.periodStart}
            weekly={data}
            days={daily.days}
            isLoading={daily.isLoading}
            hasErrors={daily.hasErrors}
            onRetry={daily.retryFailed}
          />

          <button
            type="button"
            className="performance-trend-toggle"
            aria-expanded={showTrend}
            onClick={() => setShowTrend(value => !value)}
          >
            <span>
              <Activity size={16} />
              Daily Performance Trend
            </span>

            {showTrend
              ? <ChevronUp size={16} />
              : <ChevronDown size={16} />}
          </button>

          {showTrend && (
            <MetricTrendChart
              metrics={data.metrics}
              days={daily.days}
              isLoading={daily.isLoading}
              hasErrors={daily.hasErrors}
              onRetry={daily.retryFailed}
            />
          )}

          <div className="analytical-metadata">
            Data refreshed:{' '}
            {new Date(data.dataRefreshedAt).toLocaleString(
              'en-CA',
              { timeZone: 'UTC' },
            )} UTC
          </div>
        </>
      )}
    </section>
  )
}
