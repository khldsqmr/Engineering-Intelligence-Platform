import { useState } from 'react'
import { Info } from 'lucide-react'

import { MetadataLabels } from '../../../../components/metadata/MetadataLabels'
import { MetricDetailDrawer } from '../../../../components/metrics/MetricDetailDrawer'

import type { AnalyticalMetric } from '../../../../types/analytics'

import { metricGroups } from '../../../../utils/metricGroups'
import { findMetric, getChangeTone } from '../../../../utils/metricFormatting'

import './lifecycle.css'

const metricLabels: Record<string, string> = {
  prsOpened: 'PRs Opened',
  prsMerged: 'PRs Merged',
  prsClosed: 'PRs Closed',
  prsClosedWithoutMerge: 'PRs Closed Without Merge',
  medianFirstReviewHours: 'Median First Review (hrs)',
  meanPreReviewHours: 'Mean Pre-Review Duration (hrs)',
  meanPostReviewHours: 'Mean Post-Review Duration (hrs)',
  preReviewTimeSharePct: 'Pre-Review Time Share (%)',
  mergedPRReviewCoveragePct: 'External Review Coverage (%)',
  uniqueExternalReviewers: 'Unique External Reviewers',
  medianMergeHours: 'Median Merge Duration (hrs)',
  p90MergeHours: 'P90 Merge Duration (hrs)',
  medianLinesChanged: 'Median Lines Changed',
  medianFilesChanged: 'Median Files Changed',
}

function formatValue(value: number | null): string {
  if (value === null || !Number.isFinite(value)) return 'N/A'
  if (value !== 0 && Math.abs(value) < 0.01) return '<0.01'

  return new Intl.NumberFormat('en-CA', {
    maximumFractionDigits: Math.abs(value) < 1 ? 2 : 1,
  }).format(value)
}

function formatChange(
  value: number | null,
  suffix = '%',
): string {
  if (value === null || !Number.isFinite(value)) return 'N/A'

  const magnitude = Math.abs(value)
  const direction = value > 0 ? '▲' : value < 0 ? '▼' : '—'

  const formatted = magnitude >= 1000
    ? new Intl.NumberFormat('en-CA', {
        notation: 'compact',
        maximumFractionDigits: 1,
      }).format(magnitude)
    : formatValue(magnitude)

  return `${direction} ${formatted}${suffix}`
}

function benchmarkTone(metric: AnalyticalMetric) {
  const change = metric.changeVsBenchmarkPct

  if (
    change === null ||
    change === 0 ||
    metric.performanceDirection === 'CONTEXT_DEPENDENT'
  ) return 'neutral'

  const favorable =
    metric.performanceDirection === 'HIGHER_IS_BETTER'
      ? change > 0
      : change < 0

  return favorable ? 'positive' : 'negative'
}

export function LifecycleDiagnostics({
  metrics,
}: {
  metrics: AnalyticalMetric[]
}) {
  const [selectedMetric, setSelectedMetric] =
    useState<AnalyticalMetric | null>(null)

  return (
    <section className="lifecycle-diagnostics">

      {metricGroups.map(group => (
        <section className="lifecycle-category" key={group.id}>

          <header className="lifecycle-category-header">
            <h3>
              <span>{group.sequence}</span>
              {group.label}
              <small className="lifecycle-metric-count">
                {group.metricIds.length}
              </small>
            </h3>

            <MetadataLabels
              source="GitHub"
              informationType="Fact"
            />
          </header>

          <div className="lifecycle-table-container">
            <table
              className="lifecycle-table"
              aria-label={group.label}
            >
              <colgroup>
                <col style={{ width: '24%' }} />
                <col style={{ width: '13%' }} />
                <col style={{ width: '13%' }} />
                <col style={{ width: '13%' }} />
                <col style={{ width: '13%' }} />
                <col style={{ width: '14%' }} />
                <col style={{ width: '10%' }} />
              </colgroup>

              <thead>
                <tr>
                  <th scope="col">Metric</th>
                  <th scope="col">Current</th>
                  <th scope="col">Previous</th>
                  <th scope="col">WoW</th>
                  <th scope="col">Benchmark</th>
                  <th scope="col">vs. Benchmark</th>
                  <th scope="col" title="Current period sample size">
                    Sample
                  </th>
                </tr>
              </thead>

              <tbody>
                {group.metricIds.map(metricId => {
                  const metric = findMetric(metrics, metricId)

                  if (!metric) return null

                  const label =
                    metricLabels[metricId] ?? metric.metricName

                  const isPercentage =
                    metric.metricUnit === 'PERCENT'

                  return (
                    <tr key={metricId}>

                      <th scope="row">
                        <div className="lifecycle-metric-name">
                          <span title={metric.metricName}>
                            {label}
                          </span>

                          <button
                            type="button"
                            className="metric-info-button"
                            title={metric.metricDescription}
                            aria-label={`Explore ${metric.metricName}`}
                            onClick={() => setSelectedMetric(metric)}
                          >
                            <Info size={12} />
                          </button>
                        </div>
                      </th>

                      <td
                        className="numeric lifecycle-current"
                        title={String(metric.currentValue ?? 'N/A')}
                      >
                        {formatValue(metric.currentValue)}
                      </td>

                      <td
                        className="numeric lifecycle-value"
                        title={String(metric.previousValue ?? 'N/A')}
                      >
                        {formatValue(metric.previousValue)}
                      </td>

                      <td
                        className="numeric lifecycle-change"
                        data-tone={getChangeTone(metric)}
                      >
                        {formatChange(
                          isPercentage
                            ? metric.changeValue
                            : metric.changePct,
                          isPercentage ? ' pp' : '%',
                        )}
                      </td>

                      <td
                        className="numeric lifecycle-value"
                        title={`${metric.historicalBenchmarkAvg ?? 'N/A'} · ${metric.benchmarkPeriodCount} historical periods`}
                      >
                        {formatValue(metric.historicalBenchmarkAvg)}
                      </td>

                      <td
                        className="numeric lifecycle-change"
                        data-tone={benchmarkTone(metric)}
                      >
                        {formatChange(metric.changeVsBenchmarkPct)}
                      </td>

                      <td
                        className="numeric lifecycle-sample"
                        title="Number of observations contributing to the current metric"
                      >
                        {formatValue(metric.sampleSize)}
                      </td>

                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

        </section>
      ))}

      <div className="lifecycle-note">
        Benchmarks use available historical periods.
        Sample sizes reflect each metric's analytical cohort.
        Coverage and methodology are available in metric details.
        N/A indicates unavailable data.
      </div>

      {selectedMetric && (
        <MetricDetailDrawer
          metric={selectedMetric}
          open={true}
          onClose={() => setSelectedMetric(null)}
        />
      )}

    </section>
  )
}
