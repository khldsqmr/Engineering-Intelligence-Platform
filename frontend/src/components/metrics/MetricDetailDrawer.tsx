import type { ReactNode } from 'react'

import {
  DetailDrawer,
} from '../common/DetailDrawer'

import {
  MetadataLabels,
} from '../metadata/MetadataLabels'

import type {
  AnalyticalMetric,
} from '../../types/analytics'

import {
  formatMetricValue,
  formatMetricChange,
  formatNumber,
  getChangeTone,
} from '../../utils/metricFormatting'

import {
  formatReportingPeriod,
} from '../../utils/reportingDates'

interface MetricDetailDrawerProps {
  metric: AnalyticalMetric
  open: boolean
  onClose: () => void
}

function DetailField({
  label,
  children,
}: {
  label: string
  children: ReactNode
}) {
  return (
    <div className="drawer-field">
      <span>{label}</span>
      <strong>{children}</strong>
    </div>
  )
}

function readable(value: string | null): string {
  return value
    ? value.replaceAll('_', ' ').toLowerCase()
    : 'N/A'
}

export function MetricDetailDrawer({
  metric,
  open,
  onClose,
}: MetricDetailDrawerProps) {
  return (
    <DetailDrawer
      open={open}
      onClose={onClose}
      title={metric.metricName}
      subtitle="METRIC EXPLORER"
    >
      <MetadataLabels
        source="GitHub"
        informationType="Fact"
      />

      <div className="drawer-metric-value numeric">
        {formatMetricValue(
          metric.currentValue,
          metric.metricUnit,
        )}
      </div>

      <div
        className="metric-tile-change"
        data-tone={getChangeTone(metric)}
      >
        {formatMetricChange(metric)}
        <span className="comparison-label">
          vs. previous period
        </span>
      </div>

      <section className="drawer-section">
        <h3>Performance</h3>

        <DetailField label="Reporting period">
          {formatReportingPeriod(metric)}
        </DetailField>

        <DetailField label="Previous period">
          {formatMetricValue(
            metric.previousValue,
            metric.metricUnit,
          )}
        </DetailField>

        <DetailField label="Historical benchmark">
          {metric.metricUnit === 'COUNT'
            ? formatNumber(metric.historicalBenchmarkAvg)
            : formatMetricValue(
                metric.historicalBenchmarkAvg,
                metric.metricUnit,
              )}
        </DetailField>

        <DetailField label="Benchmark periods">
          {metric.benchmarkPeriodCount}
        </DetailField>

        <DetailField label="Change vs. benchmark">
          {metric.changeVsBenchmarkPct === null
            ? 'N/A'
            : `${formatNumber(metric.changeVsBenchmarkPct)}%`}
        </DetailField>
      </section>

      <section className="drawer-section">
        <h3>Definition & methodology</h3>

        <p>{metric.metricDescription}</p>

        <DetailField label="Aggregation">
          {readable(metric.aggregationType)}
        </DetailField>

        <DetailField label="Analytical cohort">
          {readable(metric.analyticalCohort)}
        </DetailField>

        <DetailField label="Unit">
          {readable(metric.metricUnit)}
        </DetailField>

        <DetailField label="Period event">
          {metric.periodEventAttribute}
        </DetailField>

        <DetailField label="Performance direction">
          {readable(metric.performanceDirection)}
        </DetailField>

        <h4>Calculation</h4>
        <p>{metric.calculationDefinition}</p>

        <h4>Interpretation</h4>
        <p>{metric.interpretationGuidance}</p>
      </section>

      <section className="drawer-section">
        <h3>Data quality</h3>

        <DetailField label="Metric coverage">
          {readable(metric.coverageStatus)}
        </DetailField>

        <DetailField label="Eligible PRs">
          {formatNumber(metric.eligiblePRCount)}
        </DetailField>

        <DetailField label="Enriched PRs">
          {formatNumber(metric.enrichedPRCount)}
        </DetailField>

        <DetailField label="Sample size">
          {formatNumber(metric.sampleSize)}
        </DetailField>

        <DetailField label="Enrichment coverage">
          {formatMetricValue(
            metric.enrichmentCoveragePct,
            'PERCENT',
          )}
        </DetailField>

        <DetailField label="Detail enrichment required">
          {metric.requiresDetailEnrichment ? 'Yes' : 'No'}
        </DetailField>

        <DetailField label="Review enrichment required">
          {metric.requiresReviewEnrichment ? 'Yes' : 'No'}
        </DetailField>

        <p>
          Enrichment completeness does not imply complete
          coverage of the original repository.
        </p>
      </section>

      <section className="drawer-section">
        <h3>Source & lineage</h3>

        <DetailField label="Source">
          GitHub
        </DetailField>

        <DetailField label="Information type">
          Deterministic fact
        </DetailField>

        <DetailField label="Analytical layer">
          Gold
        </DetailField>

        <DetailField label="Semantic layer">
          Control metric registry
        </DetailField>

        <DetailField label="Source dependencies">
          {metric.sourceDependencies}
        </DetailField>

        <DetailField label="Metric ID">
          {metric.metricId}
        </DetailField>

        <DetailField label="Metric version">
          {metric.metricVersion}
        </DetailField>

        <DetailField label="Calculated at">
          {metric.calculatedAt}
        </DetailField>

        <h4>Evidence ID</h4>
        <code className="drawer-identifier">
          {metric.evidenceId}
        </code>

        <h4>Ingestion run ID</h4>
        <code className="drawer-identifier">
          {metric.ingestionRunId}
        </code>
      </section>

    </DetailDrawer>
  )
}
