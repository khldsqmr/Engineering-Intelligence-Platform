import { PageHeader } from '../../../components/layout/PageHeader'
import { ReportingPeriodFilter } from '../../../components/filters/ReportingPeriodFilter'

import { useReportingWeek } from '../../../hooks/useReportingWeek'

import { LifecycleDiagnostics } from './components/LifecycleDiagnostics'

export function EngineeringLifecyclePage() {
  const week = useReportingWeek()

  const {
    data,
    isPending,
    isError,
    refetch,
  } = week.query

  return (
    <section className="workspace-page lifecycle-workspace">

      <PageHeader
        category="Analytics"
        title="Engineering Lifecycle"
        description="Diagnose engineering activity, collaboration, delivery and code change characteristics."
      />

      <ReportingPeriodFilter week={week} />

      {isPending ? (
        <div className="empty-state" role="status">
          Loading lifecycle metrics...
        </div>
      ) : isError || !data ? (
        <div className="empty-state">
          <h2>Unable to load lifecycle metrics</h2>

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
          <LifecycleDiagnostics
            key={`${data.ingestionRunId}:${data.periodStart}`}
            metrics={data.metrics}
          />

          <div className="analytical-metadata">
            Source coverage: {data.sourceCoverage}
            {' · '}
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
