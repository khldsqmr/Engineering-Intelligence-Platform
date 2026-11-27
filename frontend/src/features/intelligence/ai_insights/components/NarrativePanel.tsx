import { useState } from 'react'

import {
  Sparkles,
  ShieldCheck,
  Info,
  LoaderCircle,
  ArrowRight,
} from 'lucide-react'

import { MetadataLabels } from '../../../../components/metadata/MetadataLabels'
import { MetricDetailDrawer } from '../../../../components/metrics/MetricDetailDrawer'

import { useNarrative } from '../../../../hooks/useNarrative'

import {
  formatMetricValue,
  formatMetricChange,
  getChangeTone,
} from '../../../../utils/metricFormatting'

import type {
  AnalyticalMetric,
  InsightsResponse,
} from '../../../../types/analytics'

import type {
  EvidenceReference,
} from '../../../../types/intelligence'

import { IntelligenceEvaluationDetails } from './IntelligenceEvaluationDetails'

import './narrative.css'

export function NarrativePanel({
  analytics,
}: {
  analytics: InsightsResponse
}) {
  const { query, generation } = useNarrative(analytics)

  const [selectedMetric, setSelectedMetric] =
    useState<AnalyticalMetric | null>(null)

  const keyMetricIds = new Set([
    'prsOpened',
    'prsMerged',
    'prsClosedWithoutMerge',
    'medianMergeHours',
    'p90MergeHours',
    'medianFirstReviewHours',
    'meanPreReviewHours',
    'mergedPRReviewCoveragePct',
  ])

  const factualMetrics = analytics.metrics.filter(
    metric => keyMetricIds.has(metric.metricId),
  )

  const result = query.data

  const approved =
    result?.status === 'AUTO_APPROVED'

  const narrative = approved
    ? result.response
    : null

  function renderReferences(
    references: EvidenceReference[],
  ) {
    if (!references.length) return null

    return (
      <div className="intelligence-references">
        {references.map(reference => {
          const evidence = result?.evidence.find(
            item => item.evidenceRef === reference.evidenceRef,
          )

          const metric = analytics.metrics.find(
            item => item.evidenceId === evidence?.evidenceId,
          )

          return (
            <button
              key={reference.evidenceRef}
              type="button"
              className="intelligence-reference"
              disabled={!metric}
              onClick={() => {
                if (metric) setSelectedMetric(metric)
              }}
              title={
                evidence?.semanticContext.metricName
                ?? reference.evidenceRef
              }
            >
              {reference.evidenceRef}
              {' · '}
              {evidence?.semanticContext.metricName
                ?? 'Evidence unavailable'}
              <ArrowRight size={10} />
            </button>
          )
        })}
      </div>
    )
  }

  return (
    <div className="intelligence-workspace-content">

      <section className="intelligence-card">

        <header className="intelligence-card-header">
          <div className="intelligence-heading">
            <Sparkles size={18} />

            <div>
              <h2>Weekly Engineering Insights</h2>
              <p>What changed, why it may have changed, and what to investigate next.</p>
            </div>
          </div>


        </header>

        <div className="intelligence-toolbar">

          <div className="intelligence-status">
            {approved && <ShieldCheck size={14} />}

            {generation.isPending
              ? 'Generation in progress'
              : query.isPending
                ? 'Retrieving intelligence'
                : query.isError
                  ? 'Intelligence unavailable'
                  : approved
                    ? 'Auto-approved'
                    : (result?.status ?? 'NOT_GENERATED')
                        .replaceAll('_', ' ')}
          </div>

          <button
            type="button"
            className="intelligence-generate-button"
            disabled={
              approved ||
              generation.isPending ||
              query.isPending ||
              query.isError
            }
            onClick={() => generation.mutate()}
          >
            {generation.isPending
              ? <LoaderCircle size={14} className="intelligence-spinner" />
              : <Sparkles size={14} />}

            {generation.isPending
              ? 'Generating...'
              : approved
                ? 'Intelligence available'
                : 'Generate intelligence'}
          </button>

        </div>

        {query.isError && (
          <div className="intelligence-notice" role="alert">
            Unable to retrieve intelligence.

            <button
              type="button"
              onClick={() => void query.refetch()}
            >
              Retry
            </button>
          </div>
        )}

        {generation.isError && (
          <div className="intelligence-notice" role="alert">
            Intelligence generation could not be completed.
            Please try again.
          </div>
        )}

        {generation.isPending && (
          <div className="intelligence-notice" role="status">
            Building analytical context, generating the narrative
            and evaluating its supporting evidence.
          </div>
        )}

        {!approved &&
          !generation.isPending &&
          !query.isPending &&
          !query.isError && (
            <div className="intelligence-notice">
              {result?.status === 'NOT_GENERATED'
                ? 'No intelligence has been generated for this reporting period.'
                : 'No approved narrative is available for this reporting period.'}
            </div>
        )}

      </section>


      <div
        className={
          approved
            ? 'intelligence-split-layout'
            : 'intelligence-split-layout intelligence-facts-only'
        }
      >

        <div className="intelligence-primary-column">

          {narrative?.status === 'INSUFFICIENT_EVIDENCE' && (
          <div className="intelligence-notice">
            Available evidence is insufficient to support
            a reliable analytical conclusion.
          </div>
        )}

        {narrative?.narrative && (
          <section className="intelligence-card intelligence-analysis-section">
            <div className="intelligence-section-title">
              <h3>
                <span>01</span>
                Performance Observation
              </h3>

              <span className="intelligence-type-label">
                <Sparkles size={10} aria-hidden="true" />
                AI Selected · Gold Rendered
              </span>
            </div>

            <p className="intelligence-section-question">
              What changed during the reporting period?
            </p>

            <p>{narrative.narrative.text}</p>

            {renderReferences(
              narrative.narrative.supportingEvidence,
            )}
            <div className="intelligence-ai-purpose">
              <Info size={12} aria-hidden="true" />
              <span>
                <strong>How AI is used:</strong> Selects a noteworthy metric movement. Numerical values and directions are rendered directly from Gold.
              </span>
            </div>
          </section>
        )}

        {narrative?.hypothesis && (
          <section className="intelligence-card intelligence-analysis-section">
            <div className="intelligence-section-title">
              <h3>
                <span>02</span>
                Root-Cause Hypothesis
              </h3>

              <span className="intelligence-type-label">
                <Sparkles size={10} aria-hidden="true" />
                AI Generated
              </span>
            </div>

            <p className="intelligence-section-question">
              What might explain the observed changes?
            </p>

            <p>{narrative.hypothesis.text}</p>

            <span className="intelligence-qualification">
              Potential explanation requiring further investigation.
            </span>

            <h4>Supporting Evidence</h4>

            {renderReferences(
              narrative.hypothesis.supportingEvidence,
            )}

            <h4>Counter-Evidence</h4>

            {narrative.hypothesis.counterEvidence.length
              ? renderReferences(
                  narrative.hypothesis.counterEvidence,
                )
              : <p>No counter-evidence cited.</p>}
            <div className="intelligence-ai-purpose">
              <Info size={12} aria-hidden="true" />
              <span>
                <strong>How AI is used:</strong> Examines relationships between metrics to formulate plausible explanations supported by available evidence.
              </span>
            </div>
          </section>
        )}

        {!!narrative?.alternativeExplanations.length && (
          <section className="intelligence-card intelligence-analysis-section">
            <div className="intelligence-section-title">
              <h3>
                <span></span>
                Alternative Explanations
              </h3>

              <span className="intelligence-type-label">
                <Sparkles size={10} aria-hidden="true" />
                AI Generated
              </span>
            </div>

            <p className="intelligence-section-question">
              What other factors could explain these observations?
            </p>

            <ul>
              {narrative.alternativeExplanations.map(
                (explanation, index) => (
                  <li key={index}>{explanation}</li>
                ),
              )}
            </ul>
            <div className="intelligence-ai-purpose">
              <Info size={12} aria-hidden="true" />
              <span>
                <strong>How AI is used:</strong> Considers competing explanations to avoid relying on a single interpretation.
              </span>
            </div>
          </section>
        )}

        {narrative?.recommendedInvestigation && (
          <section className="intelligence-card intelligence-analysis-section">
            <div className="intelligence-section-title">
              <h3>
                <span>03</span>
                Recommended Investigation
              </h3>

              <span className="intelligence-type-label">
                <Sparkles size={10} aria-hidden="true" />
                AI Generated
              </span>
            </div>

            <p className="intelligence-section-question">
              What should the engineering team investigate next?
            </p>

            <p>{narrative.recommendedInvestigation}</p>
            <div className="intelligence-ai-purpose">
              <Info size={12} aria-hidden="true" />
              <span>
                <strong>How AI is used:</strong> Proposes investigative next steps based on observations and unresolved hypotheses.
              </span>
            </div>
          </section>
        )}

      {approved && result && (
        <section className="intelligence-card">

          <div className="intelligence-section-title">
            <h3>
              <span>04</span>
              Intelligence Assessment
            </h3>
          </div>

          <p className="intelligence-section-question">
            How was the response evaluated, and how strong is its evidence?
          </p>
        {approved && result && (
          <div className="intelligence-assessment">



            <p className="intelligence-assessment-description">
              Response quality evaluates the AI's interpretation.
              Evidence confidence assesses the strength of the
              available data. A high evaluation score does not
              establish causation.
            </p>

            <div className="intelligence-score-grid">

            <div className="intelligence-score">
              <div className="intelligence-score-label">
                {result.evaluatorModel === 'deterministic-report'
                  ? 'Report Validation'
                  : 'AI Response Quality'}
                <span className="intelligence-assessment-label">
                  {result.evaluatorModel === 'deterministic-report'
                    ? 'Deterministic'
                    : 'Model-based'}
                </span>
                <Info
                  size={12}
                  aria-label="Evaluation method and validation result"
                />
              </div>

              <strong>
                {result.evaluatorModel === 'deterministic-report'
                  ? 'Passed'
                  : (result.evaluationScore ?? 'N/A')}
                {result.evaluatorModel !== 'deterministic-report' &&
                  result.evaluationScore !== null && <small>/100</small>}
              </strong>

              <p>{result.evaluatorModel === 'deterministic-report'
                ? 'Passed application-controlled evidence and report validation.'
                : 'Model-based assessment of the interpretation of evidence.'}</p>
            </div>

            <div className="intelligence-score">
              <div className="intelligence-score-label">
                Heuristic Confidence
                <span className="intelligence-assessment-label">
                  Rule-based
                </span>
                <Info
                  size={12}
                  aria-label="Heuristic evidence confidence, not probability"
                />
              </div>

              <strong>
                {result.confidenceScore ?? 'N/A'}
                {result.confidenceScore !== null && <small>/100</small>}
              </strong>

              <p>How strongly the available evidence supports the conclusions. Not a causal probability.</p>
            </div>

            </div>

            <IntelligenceEvaluationDetails
              intelligenceId={result.intelligenceId}
            />

          </div>
        )}


        </section>
      )}

        </div>

        <aside
          className="intelligence-reference-column"
          aria-label="Analytical evidence and metric comparisons"
        >

          {approved && result && result.evidence.length > 0 && (
        <section className="intelligence-card">

          <header className="intelligence-card-header">
            <div>
              <h2>Analytical Evidence</h2>
              <p>Actual values calculated by the analytical pipeline, not generated by AI.</p>
            </div>

            <MetadataLabels
              source="GitHub"
              informationType="Fact"
            />
          </header>

          <div className="intelligence-evidence-grid">

            {result.evidence.map(evidence => {
              const metric = analytics.metrics.find(
                item => item.evidenceId === evidence.evidenceId,
              )

              return (
                <div
                  className="intelligence-evidence-card"
                  key={evidence.evidenceRef}
                >
                  <div className="intelligence-evidence-header">
                    <span>{evidence.evidenceRef}</span>

                    <button
                      type="button"
                      className="metric-info-button"
                      disabled={!metric}
                      aria-label="Explore evidence methodology"
                      onClick={() => {
                        if (metric) setSelectedMetric(metric)
                      }}
                    >
                      <Info size={13} />
                    </button>
                  </div>

                  <h3>{evidence.semanticContext.metricName}</h3>

                  {metric ? (
                    <>
                      <div className="intelligence-evidence-value">
                        <strong>
                          {formatMetricValue(
                            metric.currentValue,
                            metric.metricUnit,
                          )}
                        </strong>

                        <span data-tone={getChangeTone(metric)}>
                          {formatMetricChange(metric)}
                        </span>
                      </div>

                      <p>
                        Previous: {' '}
                        {formatMetricValue(
                          metric.previousValue,
                          metric.metricUnit,
                        )}
                      </p>

                      <p>
                        Sample: {metric.sampleSize ?? 'N/A'}
                        {' · '}
                        {metric.coverageStatus.toLowerCase()}
                      </p>
                    </>
                  ) : (
                    <p>
                      Evidence cannot be matched to the active
                      analytical snapshot.
                    </p>
                  )}
                </div>
              )
            })}

          </div>

        </section>
      )}

          <section className="intelligence-card">

        <header className="intelligence-card-header">
          <div>
            <h2>Key Metric Comparisons</h2>
            <p>
              Governed metric values and comparisons,
              independent of AI generation.
            </p>
          </div>

          <MetadataLabels
            source="GitHub"
            informationType="Fact"
          />
        </header>

        <div className="intelligence-facts-scroll">
          <table className="intelligence-facts-table">
            <thead>
              <tr>
                <th>Metric</th>
                <th>Previous</th>
                <th>Current</th>
                <th>Change</th>
              </tr>
            </thead>

            <tbody>
              {factualMetrics.map(metric => (
                <tr key={metric.metricId}>
                  <td>
                    <button
                      type="button"
                      className="intelligence-fact-link"
                      onClick={() => setSelectedMetric(metric)}
                    >
                      {metric.metricName}
                      <ArrowRight size={11} />
                    </button>
                  </td>

                  <td>
                    {formatMetricValue(
                      metric.previousValue,
                      metric.metricUnit,
                    )}
                  </td>

                  <td>
                    <strong>
                      {formatMetricValue(
                        metric.currentValue,
                        metric.metricUnit,
                      )}
                    </strong>
                  </td>

                  <td data-tone={getChangeTone(metric)}>
                    {metric.currentValue === null ||
                     metric.previousValue === null
                      ? 'N/A'
                      : formatMetricChange(metric)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="intelligence-ai-purpose">
          <Info size={12} aria-hidden="true" />
          <span>
            <strong>Source coverage:</strong>{' '}
            {analytics.sourceCoverage.toLowerCase()}.
            {' '}Values are calculated by the analytical
            pipeline. Missing values are not treated as zero.
          </span>
        </div>

        {!approved && !generation.isPending && (
          <div className="intelligence-notice">
            AI interpretation is not currently available.
            The analytical observations above remain available
            independently of the intelligence approval process.
          </div>
        )}

      </section>

        </aside>

      </div>

      {selectedMetric && (
        <MetricDetailDrawer
          metric={selectedMetric}
          open={true}
          onClose={() => setSelectedMetric(null)}
        />
      )}

    </div>
  )
}
