import { useState } from 'react'
import { Info } from 'lucide-react'

import { MetadataLabels } from '../../../../components/metadata/MetadataLabels'
import { MetricDetailDrawer } from '../../../../components/metrics/MetricDetailDrawer'

import type {
  AnalyticalMetric,
  InsightsResponse,
  MetricUnit,
} from '../../../../types/analytics'

import type {
  DailyInsight,
} from '../../../../hooks/useDailyInsights'

import { metricGroups } from '../../../../utils/metricGroups'

import {
  findMetric,
  formatNumber,
  formatMetricChange,
  getChangeTone,
} from '../../../../utils/metricFormatting'

import './weekly-performance.css'

interface Props {
  weekly: InsightsResponse
  days: DailyInsight[]
  isLoading: boolean
  hasErrors: boolean
  onRetry: () => void
}

const units: Record<MetricUnit, string> = {
  COUNT: '',
  HOURS: 'hrs',
  PERCENT: '%',
  LINES: 'lines',
  FILES: 'files',
}

const displayNames: Record<string, string> = {
  prsOpened: 'PRs Opened',
  prsMerged: 'PRs Merged',
  prsClosed: 'PRs Closed',
  prsClosedWithoutMerge: 'PRs Closed Without Merge',
  medianFirstReviewHours: 'Median First Review',
  mergedPRReviewCoveragePct: 'External Review Coverage',
}

const aggregationLabels: Record<string, string> = {
  prsOpened: 'Sum',
  prsMerged: 'Sum',
  prsClosed: 'Sum',
  prsClosedWithoutMerge: 'Sum',
  medianFirstReviewHours: 'Median',
  meanPreReviewHours: 'Wtd. Avg',
  meanPostReviewHours: 'Wtd. Avg',
  preReviewTimeSharePct: 'Ratio',
  mergedPRReviewCoveragePct: 'Wtd. Ratio',
  uniqueExternalReviewers: 'Distinct',
  medianMergeHours: 'Median',
  p90MergeHours: 'P90',
  medianLinesChanged: 'Median',
  medianFilesChanged: 'Median',
}

function formatWeekday(date: string) {
  return new Intl.DateTimeFormat('en-CA', {
    weekday: 'short',
    timeZone: 'UTC',
  }).format(new Date(date))
}

function formatDate(date: string) {
  return new Intl.DateTimeFormat('en-CA', {
    month: 'short',
    day: 'numeric',
    timeZone: 'UTC',
  }).format(new Date(date))
}

function unavailableLabel(day: DailyInsight) {
  switch (day.state) {
    case 'PENDING': return 'Pending'
    case 'LOADING': return '...'
    case 'ERROR': return 'Error'
    default: return 'N/A'
  }
}

function formatPerformanceNumber(
  value: number | null,
): string {
  if (value === null || !Number.isFinite(value)) {
    return 'N/A'
  }

  const magnitude = Math.abs(value)

  if (magnitude > 0 && magnitude < 0.01) {
    return value < 0 ? '-<0.01' : '<0.01'
  }

  return formatNumber(
    value,
    magnitude < 1 ? 2 : 1,
  )
}

function formatPerformanceChange(
  metric: AnalyticalMetric,
): string {
  const change = metric.metricUnit === 'PERCENT'
    ? metric.changeValue
    : metric.changePct

  if (change === null || !Number.isFinite(change)) {
    return 'N/A'
  }

  const unit = metric.metricUnit === 'PERCENT'
    ? ' pp'
    : '%'

  if (change === 0) {
    return `— 0${unit}`
  }

  const direction = change > 0 ? '▲' : '▼'
  const magnitude = Math.abs(change)

  const formatted = magnitude >= 1000
    ? new Intl.NumberFormat('en-CA', {
        notation: 'compact',
        maximumFractionDigits: 1,
      }).format(magnitude)
    : formatPerformanceNumber(magnitude)

  return `${direction} ${formatted}${unit}`
}

function PerformanceCell({
  metric,
  showChanges,
  unavailable = 'N/A',
  aggregationLabel,
}: {
  metric?: AnalyticalMetric
  showChanges: boolean
  unavailable?: string
  aggregationLabel?: string
}) {
  const value = metric
    ? formatPerformanceNumber(
        metric.currentValue,
      )
    : unavailable

  const change = metric
    ? formatMetricChange(metric)
    : 'N/A'

  return (
    <div
      className="performance-cell"
      title={`${metric ? formatNumber(metric.currentValue, 6) : value} | ${aggregationLabel ? metric?.calculationDefinition : `Change: ${change}`} | ${metric?.coverageStatus ?? unavailable}`}
    >
      <strong className="numeric">
        {value}
      </strong>

      <span
        className="performance-cell-change numeric"
        data-visible={showChanges || Boolean(aggregationLabel)}
        aria-hidden={!showChanges && !aggregationLabel}
        data-tone={
          metric && !aggregationLabel ? getChangeTone(metric) : 'neutral'
        }
      >
        {aggregationLabel ?? (metric ? formatPerformanceChange(metric) : 'N/A')}
      </span>
    </div>
  )
}

export function WeeklyPerformanceMatrix({
  weekly,
  days,
  isLoading,
  hasErrors,
  onRetry,
}: Props) {
  const [selectedMetric, setSelectedMetric] =
    useState<AnalyticalMetric | null>(null)

  const [showChanges, setShowChanges] = useState(true)

  return (
    <section className="performance-matrix">

      <div className="performance-toolbar">

        <div className="performance-toolbar-heading">
          <h2>Weekly Performance</h2>

          <span>
            {weekly.metricCount} metrics · UTC
          </span>
        </div>

        <div className="performance-toolbar-controls">

          <span>Daily: DoD · WTD: Actual</span>

          <label className="performance-toggle">
            <input
              type="checkbox"
              checked={showChanges}
              onChange={event =>
                setShowChanges(event.target.checked)
              }
            />
            Show changes
          </label>

        </div>
      </div>

      {isLoading && (
        <p className="trend-status" role="status">
          Loading daily metrics...
        </p>
      )}

      {hasErrors && (
        <div className="trend-status">
          Some daily periods could not be retrieved.
          <button type="button" onClick={onRetry}>
            Retry
          </button>
        </div>
      )}

      <div className="performance-tables-scroll">

        <div className="performance-tables">

          {metricGroups.map(group => (
            <section
              className="performance-category"
              key={group.id}
              aria-labelledby={`performance-${group.id}`}
            >
              <header className="performance-category-header">

                <div className="performance-category-title">

                  <span className="performance-category-sequence">
                    {group.sequence}
                  </span>

                  <h3 id={`performance-${group.id}`}>
                    {group.label}
                  </h3>

                  <span className="performance-category-count">
                    {group.metricIds.length}
                  </span>

                </div>

                <MetadataLabels
                  source="GitHub"
                  informationType="Fact"
                />

              </header>

              <table
                className="performance-table"
                aria-labelledby={`performance-${group.id}`}
              >
                <colgroup>
                  <col className="performance-label-width" />
                  {days.map(day => (
                    <col key={day.date} />
                  ))}
                  <col className="performance-wtd-width" />
                </colgroup>

                <thead>
                  <tr>
                    <th
                      scope="col"
                      className="performance-metric-column"
                    >
                      Metric
                    </th>

                    {days.map(day => (
                      <th
                        scope="col"
                        key={day.date}
                        data-state={day.state}
                        title={`${day.date} · ${day.state}`}
                      >
                        <span className="performance-weekday">
                          {formatWeekday(day.date)}
                        </span>

                        <strong>
                          {formatDate(day.date)}
                        </strong>
                      </th>
                    ))}

                    <th
                      scope="col"
                      className="performance-wtd"
                    >
                      <span className="performance-weekday">
                        Summary
                      </span>
                      <strong>WTD</strong>
                    </th>
                  </tr>
                </thead>

                <tbody>
                  {group.metricIds.map(metricId => {
                    const metric = findMetric(
                      weekly.metrics,
                      metricId,
                    )

                    if (!metric) return null

                    const unit = units[metric.metricUnit]

                    const name =
                      displayNames[metric.metricId]
                      ?? metric.metricName

                    const label = unit
                      ? `${name} (${unit})`
                      : name

                    return (
                      <tr key={metricId}>
                        <th
                          scope="row"
                          className="performance-metric-column"
                        >
                          <div className="performance-metric-name">

                            <span title={label}>
                              {label}
                            </span>

                            <button
                              type="button"
                              className="metric-info-button"
                              title={metric.metricDescription}
                              aria-label={`Explore ${metric.metricName}`}
                              onClick={() =>
                                setSelectedMetric(metric)
                              }
                            >
                              <Info size={12} />
                            </button>

                          </div>
                        </th>

                        {days.map(day => (
                          <td
                            key={day.date}
                            data-state={day.state}
                          >
                            <PerformanceCell
                              metric={findMetric(
                                day.data?.metrics ?? [],
                                metricId,
                              )}
                              showChanges={showChanges}
                              unavailable={unavailableLabel(day)}
                            />
                          </td>
                        ))}

                        <td className="performance-wtd">
                          <PerformanceCell
                            metric={metric}
                            showChanges={false}
                            aggregationLabel={
                              aggregationLabels[metric.metricId]
                              ?? metric.aggregationType
                            }
                          />
                        </td>
                      </tr>
                    )
                  })}
                </tbody>

              </table>
            </section>
          ))}

        </div>
      </div>

      <footer className="performance-footer">
        <span>pp = percentage points</span>
        <span>N/A = unavailable</span>
        <span>Coverage: {weekly.sourceCoverage}</span>
        <span>WTD: period-level calculation</span>
      </footer>

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
