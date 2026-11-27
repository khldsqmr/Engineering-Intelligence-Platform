import {
  ChartCard,
} from '../../../../components/charts/ChartCard'

import type {
  AnalyticalMetric,
} from '../../../../types/analytics'

import {
  findMetric,
  formatMetricValue,
  formatMetricChange,
  getChangeTone,
} from '../../../../utils/metricFormatting'

export function CodeChangeChart({
  metrics,
}: {
  metrics: AnalyticalMetric[]
}) {
  const selectedMetrics = [
    findMetric(metrics, 'medianLinesChanged'),
    findMetric(metrics, 'medianFilesChanged'),
  ]

  return (
    <ChartCard
      title="Code Change Characteristics"
      description="Typical change size among merged PRs"
    >
      {selectedMetrics.map((metric, index) => (
        <div
          className="chart-stat-row"
          key={metric?.metricId ?? index}
        >
          <div>
            <span>
              {metric?.metricName ?? 'Metric unavailable'}
            </span>

            <strong className="chart-stat-value numeric">
              {metric
                ? formatMetricValue(
                    metric.currentValue,
                    metric.metricUnit,
                  )
                : 'N/A'}
            </strong>
          </div>

          <div className="chart-stat-comparison">

            <div
              className="metric-tile-change"
              data-tone={
                metric
                  ? getChangeTone(metric)
                  : 'neutral'
              }
            >
              {metric
                ? formatMetricChange(metric)
                : 'N/A'} WoW
            </div>

            <span>
              Previous:{' '}
              {metric
                ? formatMetricValue(
                    metric.previousValue,
                    metric.metricUnit,
                  )
                : 'N/A'}
            </span>

          </div>

        </div>
      ))}

      <p className="chart-note">
        Change size indicates scope, not necessarily
        complexity or developer productivity.
      </p>
    </ChartCard>
  )
}
