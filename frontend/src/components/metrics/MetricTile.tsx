import { useState } from 'react'
import type { ReactNode } from 'react'

import type {
  AnalyticalMetric,
  MetricUnit,
} from '../../types/analytics'

import {
  formatMetricValue,
  formatMetricChange,
  formatNumber,
  getChangeTone,
} from '../../utils/metricFormatting'

import {
  MetadataLabels,
} from '../metadata/MetadataLabels'

import {
  MetricTooltip,
} from './MetricTooltip'

import {
  MetricDetailDrawer,
} from './MetricDetailDrawer'

interface MetricTileProps {
  metric?: AnalyticalMetric
  label: string
  category?: string
  icon: ReactNode
  comparisonLabel?: string
}

const units: Record<MetricUnit, string> = {
  COUNT: '',
  HOURS: 'hrs',
  PERCENT: '%',
  LINES: 'lines',
  FILES: 'files',
}

export function MetricTile({
  metric,
  label,
  category,
  icon,
  comparisonLabel = 'WoW',
}: MetricTileProps) {
  const [drawerOpen, setDrawerOpen] = useState(false)

  const tone = metric
    ? getChangeTone(metric)
    : 'neutral'

  const value = metric
    ? formatNumber(
        metric.currentValue,
        metric.metricUnit === 'COUNT' ? 0 : 2,
      )
    : 'N/A'

  return (
    <article className="metric-tile">

      <div className="metric-tile-header">

        <div className="metric-tile-icon">
          {icon}
        </div>

        <MetadataLabels
          source="GitHub"
          informationType="Fact"
        />

      </div>

      <div className="metric-tile-heading">

        <span className="metric-tile-category">
          {category
            ?? metric?.metricCategory.replaceAll('_', ' ')
            ?? 'METRIC'}
        </span>

        <div className="metric-tile-title-row">

          <h2 className="metric-tile-label">
            {label}
          </h2>

          {metric && (
            <MetricTooltip
              metric={metric}
              onExplore={() => setDrawerOpen(true)}
            />
          )}

        </div>
      </div>

      <div className="metric-tile-value numeric">

        <span>{value}</span>

        {metric && value !== 'N/A' && (
          <span className="metric-tile-unit">
            {units[metric.metricUnit]}
          </span>
        )}

      </div>

      <div
        className="metric-tile-change numeric"
        data-tone={tone}
      >
        {metric
          ? formatMetricChange(metric)
          : 'N/A'}

        <span className="comparison-label">
          {comparisonLabel}
        </span>
      </div>

      <div className="metric-tile-previous">

        <span>Previous period</span>

        <strong className="numeric">
          {metric
            ? formatMetricValue(
                metric.previousValue,
                metric.metricUnit,
              )
            : 'N/A'}
        </strong>

      </div>

      {metric && (
        <MetricDetailDrawer
          metric={metric}
          open={drawerOpen}
          onClose={() => setDrawerOpen(false)}
        />
      )}

    </article>
  )
}
