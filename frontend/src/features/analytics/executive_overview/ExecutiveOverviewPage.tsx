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

export function ExecutiveOverviewPage() {
  const week = useReportingWeek()

  const {
    data,
    isPending,
    isError,
    refetch,
  } = week.query

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
