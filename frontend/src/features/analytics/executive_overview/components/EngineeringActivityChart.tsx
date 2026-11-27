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
} from '../../../../utils/metricFormatting'

export function EngineeringActivityChart({
  metrics,
}: {
  metrics: AnalyticalMetric[]
}) {
  return (
    <ChartCard
      title="Engineering Activity"
      description="Observed pull request activity by event"
    >
      <MetricComparisonChart
        rows={[
          {
            label: 'Opened',
            metric: findMetric(metrics, 'prsOpened'),
          },
          {
            label: 'Merged',
            metric: findMetric(metrics, 'prsMerged'),
          },
          {
            label: 'Closed',
            metric: findMetric(metrics, 'prsClosed'),
          },
        ]}
      />

      <p className="chart-note">
        Opened, merged and closed PRs represent separate
        event-based cohorts, not a conversion funnel.
      </p>
    </ChartCard>
  )
}
