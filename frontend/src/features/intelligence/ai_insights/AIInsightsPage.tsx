import { PageHeader } from '../../../components/layout/PageHeader'
import { ReportingPeriodFilter } from '../../../components/filters/ReportingPeriodFilter'

import { useReportingWeek } from '../../../hooks/useReportingWeek'

import { NarrativePanel } from './components/NarrativePanel'

export function AIInsightsPage() {
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
        category="Intelligence"
        title="AI Insights"
        description="Explore evidence-grounded narratives, potential root causes and recommended investigations."
      />

      <ReportingPeriodFilter week={week} />

      {isPending ? (
        <div className="empty-state" role="status">
          Loading analytical context...
        </div>
      ) : isError || !data ? (
        <div className="empty-state">
          <h2>Unable to load analytical context</h2>

          <button
            type="button"
            className="primary-button"
            onClick={() => void refetch()}
          >
            Retry
          </button>
        </div>
      ) : (
        <NarrativePanel
          key={`${data.ingestionRunId}:${data.periodStart}:${data.periodEndExclusive}`}
          analytics={data}
        />
      )}

    </section>
  )
}
