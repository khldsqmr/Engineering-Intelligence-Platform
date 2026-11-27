import {
  ChartCard,
} from '../../../../components/charts/ChartCard'

import type {
  AnalyticalMetric,
} from '../../../../types/analytics'

import {
  formatNumber,
} from '../../../../utils/metricFormatting'

export function HistoricalBenchmarkChart({
  metrics,
}: {
  metrics: AnalyticalMetric[]
}) {
  const supportedMetrics = metrics.filter(
    metric => metric.supportsHistoricalBenchmark,
  )

  return (
    <ChartCard
      title="Historical Benchmark"
      description="Current performance vs. historical period averages"
    >
      <div className="chart-table-container">

        <table className="chart-table">

          <thead>
            <tr>
              <th>Metric</th>
              <th>Current</th>
              <th>Benchmark</th>
              <th>Variance</th>
            </tr>
          </thead>

          <tbody>
            {supportedMetrics.map(metric => {
              const change = metric.changeVsBenchmarkPct

              const tone = change === null || change === 0
                || metric.performanceDirection === 'CONTEXT_DEPENDENT'
                ? 'neutral'
                : (
                    metric.performanceDirection === 'HIGHER_IS_BETTER'
                      ? change > 0
                      : change < 0
                  )
                  ? 'positive'
                  : 'negative'

              return (
                <tr key={metric.metricId}>
                  <td>{metric.metricName}</td>

                  <td className="numeric">
                    {formatNumber(metric.currentValue)}
                  </td>

                  <td
                    className="numeric"
                    title={`${metric.benchmarkPeriodCount} historical periods`}
                  >
                    {formatNumber(metric.historicalBenchmarkAvg)}
                  </td>

                  <td
                    className="numeric benchmark-variance"
                    data-tone={tone}
                  >
                    {change === null
                      ? 'N/A'
                      : `${change > 0 ? '+' : ''}${formatNumber(change)}%`}
                  </td>
                </tr>
              )
            })}
          </tbody>

        </table>

      </div>

      <p className="chart-note">
        Benchmarks use available historical periods.
        Duration metrics are measured in hours.
      </p>
    </ChartCard>
  )
}
