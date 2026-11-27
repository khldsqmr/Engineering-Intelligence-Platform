import { useState } from 'react'

import { EIPSelect } from '../../../components/common/EIPSelect'

import { PageHeader } from '../../../components/layout/PageHeader'
import { MetadataLabels } from '../../../components/metadata/MetadataLabels'
import { useInsights } from '../../../hooks/useInsights'

import './metric-catalog.css'

const categoryNames: Record<string, string> = {
  LIFECYCLE: 'Lifecycle',
  COLLABORATION: 'Collaboration',
  CODE_CHANGE: 'Code Change',
}

const sourceNames: Record<string, string> = {
  'SRC-002': 'Pull Requests',
  'SRC-003': 'Pull Request Details',
  'SRC-004': 'Pull Request Reviews',
}

const cohortNames: Record<string, string> = {
  CREATED_IN_PERIOD: 'PRs created during the reporting period',
  MERGED_IN_PERIOD: 'PRs merged during the reporting period',
  CLOSED_IN_PERIOD: 'PRs closed during the reporting period',
  CLOSED_WITHOUT_MERGE_IN_PERIOD:
    'PRs closed without merge during the reporting period',
  REVIEWED_MERGED_IN_PERIOD:
    'Merged PRs with a qualifying external review',
}

const aggregationNames: Record<string, string> = {
  COUNT_DISTINCT: 'Distinct count',
  MEDIAN: 'Median',
  MEAN: 'Arithmetic mean',
  PERCENTILE_90: '90th percentile',
  RATIO_OF_SUMS: 'Ratio of sums',
  RATIO_OF_COUNTS: 'Ratio of counts',
}

const unitNames: Record<string, string> = {
  COUNT: 'Count',
  HOURS: 'Hours',
  PERCENT: 'Percentage',
  LINES: 'Lines',
  FILES: 'Files',
}

const eventNames: Record<string, string> = {
  createdAt: 'PR creation date',
  mergedAt: 'PR merge date',
  closedAt: 'PR closure date',
}

const directionNames: Record<string, string> = {
  HIGHER_IS_BETTER: 'Higher is generally preferred',
  LOWER_IS_BETTER: 'Lower is generally preferred',
  CONTEXT_DEPENDENT: 'Depends on context',
}

function DefinitionRows({
  rows,
}: {
  rows: [string, string][]
}) {
  return (
    <dl className="mc-specifications">
      {rows.map(([label, value]) => (
        <div key={label}>
          <dt>{label}</dt>
          <dd>{value}</dd>
        </div>
      ))}
    </dl>
  )
}

export function MetricCatalogPage() {
  const query = useInsights()
  const data = query.data
  const metrics = data?.metrics ?? []

  const [selectedId, setSelectedId] =
    useState('medianMergeHours')

  const metric =
    metrics.find(item => item.metricId === selectedId)
    ?? metrics[0]

  const sources = metric
    ? metric.sourceDependencies
        .split(',')
        .map(source => source.trim())
        .filter(Boolean)
    : []

  return (
    <section className="workspace-page">

      <PageHeader
        category="Knowledge & Reference"
        title="Metric Catalog"
        description="Definitions, calculation logic and interpretation guidelines."
      />

      {query.isPending ? (
        <section className="mc-card" role="status">
          Loading metric definitions...
        </section>
      ) : query.isError || !data ? (
        <section className="mc-card" role="alert">
          Metric definitions could not be retrieved.

          <button
            type="button"
            onClick={() => void query.refetch()}
          >
            Retry
          </button>
        </section>
      ) : (
        <section className="mc-card mc-reference">

          <div className="mc-reference-selector">

            <label htmlFor="catalog-metric">
              Select metric
            </label>

            <EIPSelect
              id="catalog-metric"
              value={metric?.metricId ?? ''}
              onChange={setSelectedId}
              disabled={metrics.length === 0}
              placeholder="Select a metric"
              groups={Object.entries(categoryNames).map(
                ([category, label]) => ({
                  label,
                  options: metrics.filter(
                    item => item.metricCategory === category,
                  ).map(item => ({
                    value: item.metricId,
                    label: item.metricName,
                  })),
                }),
              )}
            />

            <span className="mc-muted">
              {metrics.length} registered metrics
            </span>

          </div>

          {metric ? (
            <>
              <div className="mc-reference-heading">

                <div className="mc-definition-top">
                  <span className="mc-category">
                    {categoryNames[metric.metricCategory]}
                  </span>

                  <span className="mc-muted">
                    Version {metric.metricVersion}
                  </span>
                </div>

                <h2>{metric.metricName}</h2>

                <p>{metric.metricDescription}</p>

                <MetadataLabels
                  source="Metric Registry"
                  informationType="Fact"
                />

              </div>

              <div className="mc-reference-columns">

                <section>
                  <h3>How it is calculated</h3>

                  <div className="mc-formula">
                    {metric.calculationDefinition}
                  </div>

                  <DefinitionRows rows={[
                    [
                      'Eligible records',
                      cohortNames[metric.analyticalCohort]
                        ?? metric.analyticalCohort,
                    ],
                    [
                      'Period filter',
                      eventNames[metric.periodEventAttribute]
                        ?? metric.periodEventAttribute,
                    ],
                    [
                      'Required enrichment',
                      metric.requiresReviewEnrichment
                        ? 'Complete PR reviews'
                        : metric.requiresDetailEnrichment
                          ? 'Complete PR details'
                          : 'Not required',
                    ],
                    [
                      'Historical benchmark',
                      metric.supportsHistoricalBenchmark
                        ? 'Mean of preceding equal-length periods'
                        : 'Not enabled',
                    ],
                  ]} />
                </section>

                <section>
                  <h3>Metric specifications</h3>

                  <DefinitionRows rows={[
                    [
                      'Source',
                      'GitHub · ' + sources.map(
                        source => sourceNames[source] ?? source,
                      ).join(', '),
                    ],
                    [
                      'Aggregation',
                      aggregationNames[metric.aggregationType]
                        ?? metric.aggregationType,
                    ],
                    [
                      'Unit',
                      unitNames[metric.metricUnit]
                        ?? metric.metricUnit,
                    ],
                    [
                      'Timezone',
                      data.reportingTimezone,
                    ],
                    [
                      'Interpretation',
                      directionNames[metric.performanceDirection]
                        ?? metric.performanceDirection,
                    ],
                    [
                      'Refresh',
                      'On pipeline execution',
                    ],
                  ]} />
                </section>

              </div>

              <div className="mc-reference-guidance">
                <h3>Things to keep in mind</h3>
                <p>{metric.interpretationGuidance}</p>
              </div>

              <details className="mc-reference-technical">

                <summary>
                  Technical metadata & source dependencies
                </summary>

                <DefinitionRows rows={[
                  ['Metric ID', metric.metricId],
                  ['Metric version', metric.metricVersion],
                  ['Analytical cohort', metric.analyticalCohort],
                  ['Period event', metric.periodEventAttribute],
                  ['Source dependencies', metric.sourceDependencies],
                  ['Aggregation type', metric.aggregationType],
                ]} />

              </details>
            </>
          ) : (
            <p>No registered metrics available.</p>
          )}

        </section>
      )}

    </section>
  )
}
