import {
  ChartCard,
} from '../../../../components/charts/ChartCard'

import {
  MetricComparisonChart,
} from '../../../../components/charts/MetricComparisonChart'

import type {
  AnalyticalMetric,
} from '../../../../types/analytics'

import {
  findMetric,
  formatMetricValue,
  formatMetricChange,
} from '../../../../utils/metricFormatting'

export function ReviewCycleChart({
  metrics,
}: {
  metrics: AnalyticalMetric[]
}) {
  const share = findMetric(
    metrics,
    'preReviewTimeSharePct',
  )

  return (
    <ChartCard
      title="Review Cycle Composition"
      description="Elapsed duration for reviewed and merged PRs"
    >
      <MetricComparisonChart
        rows={[
          {
            label: 'Mean pre-review duration',
            metric: findMetric(
              metrics,
              'meanPreReviewHours',
            ),
          },
          {
            label: 'Mean post-review duration',
            metric: findMetric(
              metrics,
              'meanPostReviewHours',
            ),
          },
        ]}
      />

      <div className="chart-summary">

        <span>Pre-review share of merge duration</span>

        <strong className="numeric">
          {formatMetricValue(
            share?.currentValue ?? null,
            'PERCENT',
          )}
        </strong>

        <span>
          {share ? formatMetricChange(share) : 'N/A'} WoW
        </span>

      </div>

      <p className="chart-note">
        Pre-review duration includes author preparation,
        draft time and elapsed waiting time.
      </p>
    </ChartCard>
  )
}
