import {
  GitPullRequest,
  GitMerge,
  Timer,
  MessageSquare,
  ShieldCheck,
  Users,
  Clock,
  GitPullRequestClosed,
} from 'lucide-react'

import {
  MetricTile,
} from '../../../../components/metrics/MetricTile'

import type {
  AnalyticalMetric,
} from '../../../../types/analytics'

import {
  findMetric,
} from '../../../../utils/metricFormatting'

const executiveMetrics = [
  {
    id: 'prsOpened',
    label: 'Pull Requests Opened',
    category: 'Engineering Activity',
    icon: GitPullRequest,
  },
  {
    id: 'prsMerged',
    label: 'Pull Requests Merged',
    category: 'Throughput',
    icon: GitMerge,
  },
  {
    id: 'medianMergeHours',
    label: 'Median Merge Duration',
    category: 'Delivery',
    icon: Timer,
  },
  {
    id: 'medianFirstReviewHours',
    label: 'Median First External Review',
    category: 'Collaboration',
    icon: MessageSquare,
  },
  {
    id: 'mergedPRReviewCoveragePct',
    label: 'External Review Coverage',
    category: 'Collaboration',
    icon: ShieldCheck,
  },
  {
    id: 'uniqueExternalReviewers',
    label: 'Unique External Reviewers',
    category: 'Collaboration',
    icon: Users,
  },
  {
    id: 'p90MergeHours',
    label: 'P90 Merge Duration',
    category: 'Delivery',
    icon: Clock,
  },
  {
    id: 'prsClosedWithoutMerge',
    label: 'PRs Closed Without Merge',
    category: 'Resolution',
    icon: GitPullRequestClosed,
  },
]

export function ExecutiveKPISummary({
  metrics,
}: {
  metrics: AnalyticalMetric[]
}) {
  return (
    <section
      className="major-kpi-grid"
      aria-label="Executive key performance indicators"
    >
      {executiveMetrics.map(item => {
        const Icon = item.icon

        return (
          <MetricTile
            key={item.id}
            label={item.label}
            category={item.category}
            metric={findMetric(metrics, item.id)}
            icon={<Icon size={18} />}
          />
        )
      })}
    </section>
  )
}
