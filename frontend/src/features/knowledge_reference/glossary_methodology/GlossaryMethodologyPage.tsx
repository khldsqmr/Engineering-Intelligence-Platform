import { ArrowRight, Filter } from 'lucide-react'
import { glossaryExamples } from './glossaryExamples'
import { useState } from 'react'

import { EIPSelect } from '../../../components/common/EIPSelect'

import { PageHeader } from '../../../components/layout/PageHeader'
import { MetadataLabels } from '../../../components/metadata/MetadataLabels'

import './glossary.css'

const sections = [
  {
    id: 'engineering',
    title: 'Engineering Terminology',
    description: 'Understanding pull requests and engineering collaboration.',
    entries: [
      {
        term: 'Pull Request (PR)',
        definition: 'A proposed code change submitted for review and integration into a repository.',
      },
      {
        term: 'Merge Duration',
        definition: 'Elapsed time between PR creation and successful merge, including waiting time, draft time and weekends.',
      },
      {
        term: 'External Review',
        definition: 'A qualifying review submitted by a human account other than the PR author.',
      },
      {
        term: 'Pre-Review Duration',
        definition: 'Elapsed time between PR creation and the first qualifying external review.',
      },
      {
        term: 'Post-Review Duration',
        definition: 'Elapsed time between the first qualifying external review and successful merge.',
      },
      {
        term: 'Review Coverage',
        definition: 'The percentage of observed merged PRs receiving at least one qualifying external review.',
      },
    ],
  },
  {
    id: 'analytics',
    title: 'Analytical Methodology',
    description: 'How reporting periods, comparisons and benchmarks are calculated.',
    entries: [
      {
        term: 'Reporting Period',
        definition: 'A rolling seven-day window using UTC, with an inclusive start date and exclusive end date.',
      },
      {
        term: 'Week-over-Week (WoW)',
        definition: 'Comparison between the current reporting week and the immediately preceding equal-length week.',
      },
      {
        term: 'Historical Benchmark',
        definition: 'The arithmetic mean of the preceding configured reporting-period values. All required periods must be available. This is an observed baseline, not a performance target.',
      },
      {
        term: 'Benchmark Variance',
        definition: 'The relative difference between the current metric value and its historical benchmark. Unavailable when the benchmark is missing or zero.',
      },
      {
        term: 'Percentage Point (pp)',
        definition: 'The absolute difference between two percentages, distinct from relative percentage change.',
      },
      {
        term: 'Median',
        definition: 'The middle value of an ordered distribution. Less sensitive to extreme observations than the arithmetic mean.',
      },
      {
        term: '90th Percentile (P90)',
        definition: 'The value at or below which approximately 90% of observations fall.',
      },
      {
        term: 'Weekly Aggregation',
        definition: 'Weekly metrics are calculated using the underlying reporting cohort. Weekly medians, percentiles and distinct counts are not calculated by averaging daily values.',
      },
      {
        term: 'Missing Values',
        definition: 'Unavailable or inapplicable observations are represented as N/A rather than zero.',
      },
    ],
  },
  {
    id: 'architecture',
    title: 'Data Architecture & Quality',
    description: 'How engineering observations become governed analytical facts.',
    entries: [
      {
        term: 'Control Layer',
        definition: 'Centralized pipeline configuration, source definitions, metric registry and ingestion execution metadata.',
      },
      {
        term: 'Bronze Layer',
        definition: 'Raw GitHub API observations retained with ingestion identifiers for traceability.',
      },
      {
        term: 'Silver Layer',
        definition: 'Validated, standardized and deduplicated repository, pull request and review records.',
      },
      {
        term: 'Gold Layer',
        definition: 'Deterministically calculated lifecycle facts, period metrics and historical comparisons.',
      },
      {
        term: 'Enrichment',
        definition: 'Additional PR detail and review extraction required for collaboration and code-change metrics.',
      },
      {
        term: 'Source Coverage',
        definition: 'The completeness classification of retrieved source observations. Estimated coverage does not guarantee exhaustive GitHub activity.',
      },
      {
        term: 'Enrichment Coverage',
        definition: 'The proportion of eligible pull requests with the additional information required for a metric. Complete enrichment does not imply complete source coverage.',
      },
      {
        term: 'Metric Registry',
        definition: 'The governed reference for metric definitions, calculations, units, dependencies and interpretation rules.',
      },
    ],
  },
  {
    id: 'intelligence',
    title: 'Intelligence Framework',
    description: 'How analytical evidence is transformed into AI-generated insights.',
    entries: [
      {
        term: 'Context Engineering',
        definition: 'Assembling structured temporal, semantic, analytical, relational, quality, historical and user-intent context before model generation.',
      },
      {
        term: 'Semantic Context',
        definition: 'Governed metric definitions, calculation logic, units and interpretation guidance supplied to the model.',
      },
      {
        term: 'Analytical Context',
        definition: 'Deterministic metric values, comparisons, benchmarks, sample sizes and evidence identifiers.',
      },
      {
        term: 'Relational Context',
        definition: 'Explicit relationships between metrics that guide interpretation without establishing causation.',
      },
      {
        term: 'Evidence Grounding',
        definition: 'Connecting generated observations and hypotheses to identifiable analytical facts.',
      },
      {
        term: 'Root-Cause Hypothesis',
        definition: 'A possible explanation supported by available evidence. It is not a confirmed causal finding.',
      },
      {
        term: 'Historical Intelligence',
        definition: 'Eligible approved narratives from earlier reporting periods retrieved to provide additional context. Retrieval does not retrain the model.',
      },
      {
        term: 'Persistent Cache',
        definition: 'Reuse of a compatible approved generation when the underlying context and generation configuration match.',
      },
    ],
  },
  {
    id: 'governance',
    title: 'AI Evaluation & Governance',
    description: 'Understanding quality safeguards, confidence and approval decisions.',
    entries: [
      {
        term: 'Deterministic Validation',
        definition: 'Rule-based checks of response structure, evidence references, cited directions and numerical text restrictions.',
      },
      {
        term: 'LLM Evaluation',
        definition: 'Model-based assessment of factual consistency, grounding, reasoning, counter-evidence, uncertainty and relevance.',
      },
      {
        term: 'AI Quality Score',
        definition: 'A weighted evaluation score between zero and one hundred. A high score does not guarantee factual correctness.',
      },
      {
        term: 'Evidence Confidence',
        definition: 'A rule-based assessment incorporating coverage, sample adequacy, supporting evidence, counter-evidence and historical consistency. It is not a calibrated probability.',
      },
      {
        term: 'Auto-Approval',
        definition: 'A generation that satisfies the configured deterministic and model-based evaluation gates.',
      },
      {
        term: 'Generation Archive',
        definition: 'Unapproved generation records retained for diagnostics and audit. These are excluded from the approved intelligence library and historical reuse.',
      },
      {
        term: 'Counter-Evidence',
        definition: 'Available observations that challenge or weaken a proposed explanation.',
      },
      {
        term: 'AI Limitations',
        definition: 'Model-generated interpretations and evaluations can contain errors. Observational evidence cannot independently establish causation, and important conclusions require human verification.',
      },
    ],
  },
  {
    id: 'information',
    title: 'Information Classification',
    description: 'Understanding the information labels displayed across EIP.',
    entries: [
      {
        term: 'Fact',
        definition: 'Observed source information or deterministically calculated analytical values.',
      },
      {
        term: 'Derived',
        definition: 'Information calculated from underlying facts using defined comparison or assessment logic.',
      },
      {
        term: 'AI Generated',
        definition: 'Model-generated interpretation, hypothesis or evaluation rather than an independently verified fact.',
      },
      {
        term: 'Forecast',
        definition: 'An estimated future outcome. This classification does not imply forecasting is implemented.',
      },
      {
        term: 'Target',
        definition: 'A defined desired outcome or performance objective, distinct from observed historical benchmarks.',
      },
    ],
  },
]

export function GlossaryMethodologyPage() {
  const [selectedCategory, setSelectedCategory] =
    useState('engineering')

  const [selectedTerm, setSelectedTerm] =
    useState('Pull Request (PR)')

  const section =
    sections.find(item => item.id === selectedCategory)
    ?? sections[0]

  const entry =
    section.entries.find(item => item.term === selectedTerm)
    ?? section.entries[0]

  const example = glossaryExamples[entry.term]

  function changeCategory(value: string) {
    const next = sections.find(item => item.id === value)

    if (!next) return

    setSelectedCategory(next.id)
    setSelectedTerm(next.entries[0].term)
  }

  return (
    <section className="workspace-page">

      <PageHeader
        category="Knowledge & Reference"
        title="Glossary & Methodology"
        description="Understand platform terminology through definitions and practical examples."
      />

      <section
        className="glossary-panel"
        data-category={section.id}
      >

        <div className="glossary-selectors">

          <div className="glossary-field">
            <label htmlFor="glossary-category">
              01 · Category
            </label>

            <EIPSelect
              id="glossary-category"
              value={selectedCategory}
              onChange={changeCategory}
              groups={[{
                options: sections.map(item => ({
                  value: item.id,
                  label: item.title,
                })),
              }]}
            />
            <span className="glossary-field-hint">
              Select a knowledge area
            </span>
          </div>

          <div
            className="glossary-dependency"
            aria-hidden="true"
          >
            <ArrowRight size={18} />
          </div>

          <div className="glossary-field">
            <label htmlFor="glossary-item">
              02 · Glossary Item
            </label>

            <EIPSelect
              id="glossary-item"
              value={entry.term}
              onChange={setSelectedTerm}
              groups={[{
                options: section.entries.map(item => ({
                  value: item.term,
                  label: item.term,
                })),
              }]}
            />

            <span
              className="glossary-field-hint"
              aria-live="polite"
            >
              <Filter size={11} aria-hidden="true" />
              {section.entries.length} items in selected category
            </span>
          </div>

        </div>

        <div className="glossary-reference-header">

          <div>
            <span className="glossary-category">
              {section.title}
            </span>

            <h2>{entry.term}</h2>
          </div>

          <MetadataLabels
            source="EIP Methodology"
            informationType="Fact"
          />

        </div>

        <div className="glossary-reference-section">
          <h3>What does it mean?</h3>
          <p>{entry.definition}</p>
        </div>

        {example && (
          <>
            <div className="glossary-reference-section">

              <h3>Practical example</h3>

              <p>{example.example}</p>

              {example.calculation && (
                <div className="glossary-calculation">
                  {example.calculation}
                </div>
              )}

              <small className="glossary-example-caption">
                Illustrative example · Not live reporting data
              </small>

            </div>

            {example.note && (
              <div className="glossary-reference-section">
                <h3>Things to keep in mind</h3>
                <p>{example.note}</p>
              </div>
            )}
          </>
        )}

      </section>

    </section>
  )
}
