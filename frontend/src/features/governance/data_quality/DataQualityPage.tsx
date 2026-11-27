import { useQuery } from '@tanstack/react-query'
import { RefreshCw } from 'lucide-react'

import { PageHeader } from '../../../components/layout/PageHeader'
import { ReportingPeriodFilter } from '../../../components/filters/ReportingPeriodFilter'
import { MetadataLabels } from '../../../components/metadata/MetadataLabels'
import { useReportingWeek } from '../../../hooks/useReportingWeek'
import { getIntelligenceContext } from '../../../services/intelligenceService'

import './components/data-quality.css'

function formatDate(value: string) {
  return new Date(value).toLocaleDateString('en-CA', {
    timeZone: 'UTC',
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

function daysBetween(start: string, end: string) {
  return Math.round(
    (Date.parse(end) - Date.parse(start)) / 86400000,
  )
}

function formatValue(value: number | null | undefined) {
  return value == null ? 'N/A' : value.toLocaleString('en-CA')
}

function formatStatus(value: string | null | undefined) {
  return (value ?? 'Unavailable').replaceAll('_', ' ')
}

export function DataQualityPage() {
  const week = useReportingWeek()
  const { query, period } = week
  const data = query.data

  const contextQuery = useQuery({
    queryKey: [
      'intelligence-context',
      data?.repository,
      data?.ingestionRunId,
      period?.periodStart,
      period?.periodEndExclusive,
    ],

    queryFn: ({ signal }) => {
      if (!period) {
        throw new Error('Reporting period unavailable.')
      }

      return getIntelligenceContext(period, signal)
    },

    enabled: Boolean(data && period),
  })

  const context = contextQuery.data

  const matchingContext =
    context &&
    data &&
    context.repository === data.repository &&
    context.ingestionRunId === data.ingestionRunId &&
    context.temporalContext.periodStart === data.periodStart &&
    context.temporalContext.periodEndExclusive === data.periodEndExclusive

  const metrics = data?.metrics ?? []

  const available = metrics.filter(
    metric => metric.currentValue != null,
  ).length

  const comparable = metrics.filter(
    metric =>
      metric.currentValue != null &&
      metric.previousValue != null,
  ).length

  const enrichment = metrics.filter(
    metric =>
      metric.requiresDetailEnrichment ||
      metric.requiresReviewEnrichment,
  )

  const fullyEnriched = enrichment.filter(
    metric => metric.enrichmentCoveragePct === 100,
  ).length

  const benchmarkEligible = metrics.filter(
    metric => metric.supportsHistoricalBenchmark,
  )

  const benchmarkAvailable = benchmarkEligible.filter(
    metric => metric.historicalBenchmarkAvg != null,
  ).length

  const historyDays = data
    ? daysBetween(
        data.availableHistory.start,
        data.availableHistory.endExclusive,
      )
    : 0

  const enrichmentDays = data?.availableHistory.enrichmentStart
    ? daysBetween(
        data.availableHistory.enrichmentStart,
        data.availableHistory.endExclusive,
      )
    : 0

  const enrichmentWidth = historyDays > 0
    ? Math.min(100, Math.max(0, enrichmentDays / historyDays * 100))
    : 0

  const checks = [
    {
      name: 'Current period metrics',
      available,
      total: metrics.length,
    },
    {
      name: 'Previous period comparison',
      available: comparable,
      total: metrics.length,
    },
    {
      name: 'Detailed metric enrichment',
      available: fullyEnriched,
      total: enrichment.length,
    },
    {
      name: 'Historical benchmark availability',
      available: benchmarkAvailable,
      total: benchmarkEligible.length,
    },
  ]

  function refresh() {
    void query.refetch()

    if (data && period) {
      void contextQuery.refetch()
    }
  }

  return (
    <section className="workspace-page">

      <PageHeader
        category="Governance"
        title="Data Quality"
        description="Understand data availability, historical coverage and analytical readiness."
        actions={<ReportingPeriodFilter week={week} />}
      />

      {query.isPending ? (
        <div className="dq-card" role="status">
          Loading data quality...
        </div>
      ) : query.isError || !data ? (
        <div className="dq-card" role="alert">
          Unable to retrieve data quality.

          <button
            type="button"
            className="dq-refresh"
            onClick={refresh}
          >
            Retry
          </button>
        </div>
      ) : (
        <>
          <div className="dq-simple-summary">

            <section className="dq-card">
              <span className="dq-simple-label">Data Freshness</span>

              <strong className="dq-simple-value">
                {formatDate(data.dataRefreshedAt)}
              </strong>

              <small>Last published data refresh</small>

              <MetadataLabels
                source="Ingestion Metadata"
                informationType="Fact"
              />
            </section>

            <section className="dq-card">
              <span className="dq-simple-label">Metric Availability</span>

              <strong className="dq-simple-value">
                {available} / {metrics.length}
              </strong>

              <small>Current period metrics available</small>

              <MetadataLabels
                source="Gold Analytical Layer"
                informationType="Derived"
              />
            </section>

            <section className="dq-card">
              <span className="dq-simple-label">Source Coverage</span>

              <strong className="dq-simple-value">
                {formatStatus(data.sourceCoverage)}
              </strong>

              <small>
                {data.sourceCoverage === 'ESTIMATED'
                  ? 'Completeness not confirmed'
                  : 'Published coverage classification'}
              </small>

              <MetadataLabels
                source="Ingestion Metadata"
                informationType="Fact"
              />
            </section>

          </div>

          <section className="dq-card">

            <header className="dq-card-header">
              <div>
                <h2>Historical Coverage</h2>

                <MetadataLabels
                  source="Ingestion Metadata"
                  informationType="Fact"
                />
              </div>

              <button
                type="button"
                className="dq-refresh"
                disabled={query.isFetching || contextQuery.isFetching}
                onClick={refresh}
              >
                <RefreshCw size={13} />
                Refresh
              </button>
            </header>

            <div className="dq-history-label">
              <span>Pull request lifecycle history</span>
              <strong>{historyDays} days</strong>
            </div>

            <div className="dq-history-track">
              <span style={{ width: '100%' }} />
            </div>

            <div className="dq-history-label">
              <span>Detailed review & code-change history</span>
              <strong>{enrichmentDays} days</strong>
            </div>

            <div className="dq-history-track dq-history-enrichment">
              <span style={{ width: `${enrichmentWidth}%` }} />
            </div>

            <p className="dq-footnote">
              Detailed enrichment supports review and code-change
              analysis. Available history represents the configured
              published window, not guaranteed source completeness.
            </p>

          </section>

          <section className="dq-card">

            <header className="dq-card-header">
              <div>
                <h2>Metric Readiness</h2>

                <MetadataLabels
                  source="Gold Analytical Layer"
                  informationType="Derived"
                />
              </div>
            </header>

            <div className="dq-table-scroll">
              <table className="dq-table dq-summary-table">
                <thead>
                  <tr>
                    <th scope="col">Quality Check</th>
                    <th scope="col">Available</th>
                    <th scope="col">Status</th>
                  </tr>
                </thead>

                <tbody>
                  {checks.map(check => (
                    <tr key={check.name}>
                      <th scope="row">{check.name}</th>

                      <td>
                        {check.available} / {check.total}
                      </td>

                      <td>
                        <span
                          className="dq-readiness-status"
                          data-complete={
                            check.total > 0 &&
                            check.available === check.total
                          }
                        >
                          {check.total === 0
                            ? 'Not applicable'
                            : check.available === check.total
                              ? 'Available'
                              : check.available === 0
                                ? 'Unavailable'
                                : 'Limited'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <p className="dq-footnote">
              Benchmark availability is measured against
              benchmark-enabled metrics only.
              Full enrichment does not establish complete source coverage.
            </p>

            <details className="dq-run-details">
              <summary>Explore metric-level quality details</summary>

              <div className="dq-table-scroll">
                <table className="dq-table dq-detail-table">
                  <thead>
                    <tr>
                      <th scope="col">Metric</th>
                      <th scope="col">Sample</th>
                      <th scope="col">Enrichment</th>
                      <th scope="col">Benchmark Weeks</th>
                      <th scope="col">Coverage</th>
                    </tr>
                  </thead>

                  <tbody>
                    {metrics.map(metric => (
                      <tr key={metric.metricId}>
                        <th scope="row">{metric.metricName}</th>

                        <td>{formatValue(metric.sampleSize)}</td>

                        <td>
                          {metric.requiresDetailEnrichment ||
                          metric.requiresReviewEnrichment
                            ? metric.enrichmentCoveragePct == null
                              ? 'N/A'
                              : `${formatValue(metric.enrichmentCoveragePct)}%`
                            : 'Not required'}
                        </td>

                        <td>
                          {metric.supportsHistoricalBenchmark
                            ? metric.benchmarkPeriodCount
                            : 'Not enabled'}
                        </td>

                        <td>{formatStatus(metric.coverageStatus)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </details>

            <details className="dq-run-details">
              <summary>View analytical limitations</summary>

              <div className="dq-expanded-content">
                <MetadataLabels
                  source="Quality Context"
                  informationType="Derived"
                />

                {contextQuery.isPending ? (
                  <p>Loading limitations...</p>
                ) : contextQuery.isError || !matchingContext ? (
                  <p>Quality context unavailable or mismatched.</p>
                ) : context.qualityContext.limitations.length === 0 ? (
                  <p>No explicit limitations returned.</p>
                ) : (
                  <ul>
                    {context.qualityContext.limitations.map(
                      (limitation, index) => (
                        <li key={`${index}-${limitation}`}>
                          {limitation}
                        </li>
                      ),
                    )}
                  </ul>
                )}
              </div>
            </details>

            <details className="dq-run-details">
              <summary>View ingestion information</summary>

              <dl>
                <dt>Repository</dt>
                <dd>{data.repository}</dd>

                <dt>Ingestion run</dt>
                <dd>{data.ingestionRunId}</dd>

                <dt>Last refresh</dt>
                <dd>{data.dataRefreshedAt}</dd>

                <dt>Reporting timezone</dt>
                <dd>{data.reportingTimezone}</dd>
              </dl>
            </details>

          </section>
        </>
      )}

    </section>
  )
}
