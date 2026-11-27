import { Database, Info } from 'lucide-react'
import { Link } from 'react-router-dom'

import type { IntelligenceContext } from '../../../../types/context'
import type { ContextNode } from './ContextArchitecture'

const definitions: Record<
  ContextNode,
  { title: string; source: string; purpose: string }
> = {
  sources: {
    title: 'Information Sources',
    source: 'Data & Control Layers',
    purpose: 'Collects engineering facts, metric definitions and relevant intelligence history.',
  },
  assembly: {
    title: 'Context Engineering',
    source: 'Context Assembly Service',
    purpose: 'Organizes the information required for meaningful and evidence-grounded AI reasoning.',
  },
  temporal: {
    title: 'Temporal Context',
    source: 'Reporting Period',
    purpose: 'Ensures the AI understands which reporting periods are being compared.',
  },
  semantic: {
    title: 'Semantic Context',
    source: 'Metric Registry',
    purpose: 'Explains what each metric means, how it is calculated and how it should be interpreted.',
  },
  analytical: {
    title: 'Analytical Context',
    source: 'Gold Metric Facts',
    purpose: 'Provides deterministic numerical evidence. The AI interprets the numbers rather than calculating them.',
  },
  relational: {
    title: 'Relational Context',
    source: 'Metric Relationship Rules',
    purpose: 'Helps the AI understand how metrics relate to each other without assuming causation.',
  },
  quality: {
    title: 'Quality Context',
    source: 'Ingestion & Coverage Metadata',
    purpose: 'Communicates limitations that should constrain the conclusions drawn by the AI.',
  },
  historical: {
    title: 'Historical Context',
    source: 'Approved Intelligence History',
    purpose: 'Supplies eligible earlier intelligence so the AI can consider previous observations.',
  },
  intent: {
    title: 'User Intent',
    source: 'Intelligence Request',
    purpose: 'Defines the analytical objective and expected type of response.',
  },
  generation: {
    title: 'AI Intelligence Generation',
    source: 'Generator LLM',
    purpose: 'Interprets the supplied context to produce observations, potential explanations and recommended investigations.',
  },
  assessment: {
    title: 'Intelligence Assessment',
    source: 'Validation & Evaluation Framework',
    purpose: 'Checks the generated response and independently assesses the strength of its evidence.',
  },
  history: {
    title: 'Intelligence History',
    source: 'Intelligence History Store',
    purpose: 'Persists generation results for auditability and retrieves eligible approved intelligence for future context.',
  },
}

function formatValue(value: number | null): string {
  if (value === null || !Number.isFinite(value)) return 'N/A'

  return new Intl.NumberFormat('en-CA', {
    maximumFractionDigits: 2,
  }).format(value)
}

function periodLabel(start: string, end: string): string {
  const last = new Date(`${end.slice(0, 10)}T00:00:00Z`)
  last.setUTCDate(last.getUTCDate() - 1)

  return `${start.slice(0, 10)} to ${last.toISOString().slice(0, 10)}`
}

function KeyValues({ rows }: { rows: [string, string][] }) {
  return (
    <dl className="context-key-values">
      {rows.map(([label, value]) => (
        <div key={label}>
          <dt>{label}</dt>
          <dd>{value}</dd>
        </div>
      ))}
    </dl>
  )
}

export function ContextInspector({
  context,
  selected,
}: {
  context: IntelligenceContext
  selected: ContextNode
}) {
  const definition = definitions[selected]
  const temporal = context.temporalContext

  function metricName(metricId: string) {
    return context.semanticContext.find(
      metric => metric.metricId === metricId,
    )?.metricName ?? metricId
  }

  return (
    <section className="context-card context-inspector">

      <header className="context-card-header">
        <div className="context-inspector-breadcrumb">
          <span className="context-selection-dot" />
          Exploring
          <span className="context-breadcrumb-divider">/</span>
          {[
            'temporal',
            'semantic',
            'analytical',
            'relational',
            'quality',
            'historical',
            'intent',
          ].includes(selected)
            ? 'Context Engineering'
            : 'Intelligence Architecture'}
        </div>

        <h2>{definition.title}</h2>

        <span className="context-source-label">
          <Database size={10} />
          Source: {definition.source}
        </span>

        <div className="context-inspector-purpose">
          <strong>Why is this needed?</strong>
          <p>{definition.purpose}</p>
        </div>
      </header>

      {selected === 'sources' && (
        <>
          <div className="context-mini-flow">
            <span>GitHub</span>
            <span aria-hidden="true">→</span>
            <span>Bronze</span>
            <span aria-hidden="true">→</span>
            <span>Silver</span>
            <span aria-hidden="true">→</span>
            <span>Gold</span>
          </div>

          <KeyValues rows={[
            ['Repository', context.repository],
            ['Gold metric facts', String(context.analyticalContext.length)],
            ['Metric registry', String(context.semanticContext.length)],
            ['Relationship rules', String(context.relationalContext.length)],
            ['Eligible historical insights', String(context.historicalContext.length)],
            ['Source coverage', context.qualityContext.sourceCoverage],
          ]} />
        </>
      )}

      {selected === 'assembly' && (
        <>
          <h3>How context engineering works</h3>

          <div className="context-explanation-step">
            <span>01</span>
            <div>
              <strong>Understand the information</strong>
              <p>
                Metric definitions, reporting dates and the
                analysis objective establish what the AI
                needs to understand.
              </p>
              <small>Semantic · Temporal · User Intent</small>
            </div>
          </div>

          <div className="context-explanation-step">
            <span>02</span>
            <div>
              <strong>Connect the evidence</strong>
              <p>
                Engineering metrics and their relationships
                provide the factual foundation for the
                generated insights.
              </p>
              <small>Analytical · Relational</small>
            </div>
          </div>

          <div className="context-explanation-step">
            <span>03</span>
            <div>
              <strong>Provide additional perspective</strong>
              <p>
                Data limitations and eligible previous
                intelligence help the model interpret
                findings without overstating conclusions.
              </p>
              <small>Quality · Historical</small>
            </div>
          </div>

          <div className="context-explanation">
            All seven layers are assembled into structured context
            before being projected into the model input.
            The language model interprets the supplied facts;
            it does not calculate the underlying engineering metrics.
          </div>

        </>
      )}

      {selected === 'temporal' && (
        <KeyValues rows={[
          [
            'Current period',
            periodLabel(
              temporal.periodStart,
              temporal.periodEndExclusive,
            ),
          ],
          [
            'Comparison period',
            periodLabel(
              temporal.previousPeriodStart,
              temporal.previousPeriodEndExclusive,
            ),
          ],
          ['Reporting timezone', temporal.timezone],
        ]} />
      )}

      {selected === 'semantic' && (
        <>
          <p className="context-section-caption">
            {context.semanticContext.length} metric definitions
          </p>

          {context.semanticContext.map(metric => (
            <details
              className="context-detail"
              key={metric.metricId}
            >
              <summary>{metric.metricName}</summary>

              <div className="context-detail-body">
                <p>{metric.metricDescription}</p>

                <KeyValues rows={[
                  ['Calculation', metric.calculationDefinition],
                  ['Unit', metric.metricUnit],
                  ['Cohort', metric.analyticalCohort],
                  ['Aggregation', metric.aggregationType],
                  ['Metric version', metric.metricVersion],
                  ['Source dependencies', metric.sourceDependencies],
                ]} />

                <div className="context-explanation">
                  {metric.interpretationGuidance}
                </div>
              </div>
            </details>
          ))}
        </>
      )}

      {selected === 'analytical' && (
        <>
          <p className="context-section-caption">
            {context.analyticalContext.length} deterministic evidence records
          </p>

          <div className="context-table-scroll">
            <table className="context-evidence-table">
              <thead>
                <tr>
                  <th scope="col">Evidence / Metric</th>
                  <th scope="col">Current</th>
                  <th scope="col">Previous</th>
                </tr>
              </thead>

              <tbody>
                {context.analyticalContext.map(evidence => (
                  <tr key={evidence.evidenceId}>
                    <th scope="row">
                      <small>{evidence.evidenceRef}</small>
                      {metricName(evidence.metricId)}
                    </th>

                    <td>{formatValue(evidence.currentValue)}</td>
                    <td>{formatValue(evidence.previousValue)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {context.analyticalContext.map(evidence => (
            <details
              key={evidence.evidenceId}
              className="context-detail"
            >
              <summary>
                {evidence.evidenceRef} · {metricName(evidence.metricId)}
              </summary>

              <div className="context-detail-body">
                <KeyValues rows={[
                  [
                    'Metric unit',
                    context.semanticContext.find(
                      metric => metric.metricId === evidence.metricId,
                    )?.metricUnit ?? 'N/A',
                  ],
                  ['Current value', String(evidence.currentValue ?? 'N/A')],
                  ['Previous value', String(evidence.previousValue ?? 'N/A')],
                  ['Change %', formatValue(evidence.changePct)],
                  ['Direction', evidence.direction],
                  ['Historical benchmark', formatValue(evidence.historicalBenchmarkAvg)],
                  ['Benchmark periods', String(evidence.benchmarkPeriodCount)],
                  ['Sample size', formatValue(evidence.sampleSize)],
                  ['Coverage', evidence.coverageStatus],
                  ['Evidence ID', evidence.evidenceId],
                ]} />
              </div>
            </details>
          ))}
        </>
      )}

      {selected === 'relational' && (
        <>
          <p className="context-section-caption">
            {context.relationalContext.length} defined relationships
          </p>

          {context.relationalContext.map(relationship => (
            <div
              className="context-relationship"
              key={relationship.relationshipId}
            >
              <strong>
                {relationship.relationshipType.replaceAll('_', ' ')}
              </strong>

              <div className="context-relationship-metrics">
                {relationship.metricIds.map(id => (
                  <span key={id}>{metricName(id)}</span>
                ))}
              </div>

              <p>{relationship.interpretation}</p>
            </div>
          ))}
        </>
      )}

      {selected === 'quality' && (
        <>
          <KeyValues rows={[
            ['Source coverage', context.qualityContext.sourceCoverage],
            ['Data refreshed', context.qualityContext.dataRefreshedAt],
            ...Object.entries(context.qualityContext.availableHistory)
              .map(([key, value]): [string, string] => [
                key,
                value ?? 'N/A',
              ]),
          ]} />

          <h3>Known limitations</h3>

          <ul className="context-list">
            {context.qualityContext.limitations.map((item, index) => (
              <li key={index}>{item}</li>
            ))}
          </ul>
        </>
      )}

      {selected === 'historical' && (
        <>
          <KeyValues rows={[
            [
              'Eligible earlier insights',
              String(context.historicalContext.length),
            ],
            ['Retrieval policy', 'Approved and compatible earlier intelligence'],
          ]} />

          {context.historicalContext.length === 0 ? (
            <div className="context-explanation">
              No eligible historical intelligence is currently
              available for this reporting period.
              Generation can still proceed using the other
              context layers.
            </div>
          ) : (
            context.historicalContext.map(item => (
              <details
                key={item.intelligenceId}
                className="context-detail"
              >
                <summary>
                  {periodLabel(item.periodStart, item.periodEndExclusive)}
                  {' · '}
                  Evaluation {item.evaluationScore}/100
                </summary>

                <div className="context-detail-body">
                  <p>{item.narrative}</p>

                  <KeyValues rows={[
                    ['Intelligence ID', item.intelligenceId],
                    ['Evaluation version', item.evaluationVersion],
                  ]} />
                </div>
              </details>
            ))
          )}

          <p className="context-footnote">
            Historical reuse retrieves earlier intelligence.
            It does not retrain the language model or modify
            the original analytical facts.
          </p>
        </>
      )}

      {selected === 'intent' && (
        <KeyValues rows={[
          ['Mode', context.userIntent.mode],
          [
            'Objective',
            context.userIntent.question ??
              'Identify meaningful engineering changes, potential explanations and next steps.',
          ],
          ['Expected output', 'Evidence-grounded intelligence'],
        ]} />
      )}

      {selected === 'generation' && (
        <>
          <div className="context-relationship">
            <strong>Performance Observation</strong>
            <p>Identifies meaningful changes in the supplied metrics.</p>
          </div>

          <div className="context-relationship">
            <strong>Root-Cause Hypothesis</strong>
            <p>Develops plausible explanations using available evidence.</p>
          </div>

          <div className="context-relationship">
            <strong>Recommended Investigation</strong>
            <p>Suggests how unresolved hypotheses could be investigated.</p>
          </div>

          <div className="context-explanation">
            These are structured outputs of narrative generation,
            not three independent AI agents.
          </div>

          <Link className="context-page-link" to="/intelligence">
            Explore AI Insights
          </Link>
        </>
      )}

      {selected === 'assessment' && (
        <>
          <div className="context-relationship">
            <strong>01 · Deterministic Validation</strong>
            <p>
              Checks evidence references, availability
              and directional consistency.
            </p>
          </div>

          <div className="context-relationship">
            <strong>02 · AI Response Evaluation</strong>
            <p>
              Evaluates factual consistency, grounding,
              reasoning and uncertainty handling.
            </p>
          </div>

          <div className="context-relationship">
            <strong>03 · Evidence Confidence</strong>
            <p>
              Applies deterministic scoring rules using coverage,
              sample adequacy and evidence strength.
            </p>
          </div>

          <Link className="context-page-link" to="/intelligence">
            Explore actual evaluation results
          </Link>
        </>
      )}

      {selected === 'history' && (
        <>
          <h3>What is recorded?</h3>

          <ul className="context-list">
            <li>Assembled context and model input</li>
            <li>Generated narrative and hypothesis</li>
            <li>Supporting evidence references</li>
            <li>Validation and evaluation results</li>
            <li>Confidence scores and limitations</li>
            <li>Model versions and execution metadata</li>
          </ul>

          <h3>What can be reused?</h3>

          <div className="context-explanation">
            Earlier intelligence must be approved, eligible
            and compatible with the current analytical context.
            Rejected responses are retained for audit purposes,
            not reused as approved historical intelligence.
          </div>

          <KeyValues rows={[
            [
              'Historical insights in current context',
              String(context.historicalContext.length),
            ],
          ]} />
        </>
      )}

      <footer className="context-inspector-footer">
        <Info size={12} />
        <span>
          Context for the selected reporting period.
          Saved generation snapshots may differ.
        </span>
      </footer>

    </section>
  )
}
