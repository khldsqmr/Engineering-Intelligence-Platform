import { Info } from 'lucide-react'

import {
  PageHeader,
} from '../../../components/layout/PageHeader'

import {
  ReportingPeriodFilter,
} from '../../../components/filters/ReportingPeriodFilter'

import {
  useReportingWeek,
} from '../../../hooks/useReportingWeek'

import {
  ExecutiveKPISummary,
} from './components/ExecutiveKPISummary'


import { EngineeringActivityChart } from './components/EngineeringActivityChart'
import { ReviewCycleChart } from './components/ReviewCycleChart'
import { CodeChangeChart } from './components/CodeChangeChart'
import { HistoricalBenchmarkChart } from './components/HistoricalBenchmarkChart'


import { MetricTrendChart } from '../../../components/charts/MetricTrendChart'
import { useDailyInsights } from '../../../hooks/useDailyInsights'

export function ExecutiveOverviewPage() {
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
    <section className="workspace-page">

      <PageHeader
        category="Analytics"
        title="Executive Overview"
        description="Monitor engineering activity, collaboration and delivery."
      />

      <ReportingPeriodFilter week={week} />

      {isPending ? (
        <div
          className="empty-state"
          role="status"
        >
          Loading engineering metrics...
        </div>

      ) : isError || !data ? (
        <div className="empty-state">

          <h2>Unable to load analytics</h2>

          <p>
            Verify backend connectivity and
            try loading the reporting period again.
          </p>

          <button
            className="primary-button"
            onClick={() => void refetch()}
          >
            Retry
          </button>

        </div>

      ) : (
        <>
          <div className="coverage-notice">

            <Info size={17} />

            <div>
              <strong>
                Source coverage: {data.sourceCoverage}
              </strong>

              <p>
                Metrics describe observed repository
                activity, not individual productivity.
                Enrichment availability varies by period.
              </p>
            </div>

          </div>

          <ExecutiveKPISummary
            metrics={data.metrics}
          />

          <MetricTrendChart
            metrics={data.metrics}
            days={daily.days}
            isLoading={daily.isLoading}
            hasErrors={daily.hasErrors}
            onRetry={daily.retryFailed}
          />

          
          <section
            className="analytics-chart-grid"
            aria-label="Executive analytical charts"
          >
            <EngineeringActivityChart metrics={data.metrics} />
            <ReviewCycleChart metrics={data.metrics} />
            <CodeChangeChart metrics={data.metrics} />
            <HistoricalBenchmarkChart metrics={data.metrics} />
          </section>

          <div className="analytical-metadata">
            Data refreshed:{' '}
            {new Date(
              data.dataRefreshedAt,
            ).toLocaleString('en-CA', {
              timeZone: 'UTC',
            })} UTC
          </div>
        </>
      )}

    </section>
  )
}
