import type {
  AnalyticalMetric,
} from '../../types/analytics'

import {
  formatMetricValue,
} from '../../utils/metricFormatting'

interface ComparisonRow {
  label: string
  metric?: AnalyticalMetric
}

export function MetricComparisonChart({
  rows,
}: {
  rows: ComparisonRow[]
}) {
  const maximum = Math.max(
    1,
    ...rows.flatMap(({ metric }) => [
      metric?.currentValue ?? 0,
      metric?.previousValue ?? 0,
    ]),
  )

  return (
    <div className="comparison-chart">

      <div className="chart-legend">
        <span>
          <i data-series="current" />
          Current week
        </span>

        <span>
          <i data-series="previous" />
          Previous week
        </span>
      </div>

      {rows.map(({ label, metric }) => (
        <div
          className="comparison-chart-group"
          key={label}
        >
          <strong>{label}</strong>

          {(['current', 'previous'] as const).map(series => {
            const value = series === 'current'
              ? metric?.currentValue
              : metric?.previousValue

            return (
              <div
                className="comparison-chart-row"
                key={series}
                aria-label={`${label}, ${series} period`}
              >
                <div
                  className="comparison-chart-track"
                  aria-hidden="true"
                >
                  {value != null && (
                    <div
                      className="comparison-chart-bar"
                      data-series={series}
                      style={{
                        width: `${value / maximum * 100}%`,
                      }}
                    />
                  )}
                </div>

                <span className="numeric">
                  {metric
                    ? formatMetricValue(
                        value ?? null,
                        metric.metricUnit,
                      )
                    : 'N/A'}
                </span>

              </div>
            )
          })}
        </div>
      ))}

    </div>
  )
}
