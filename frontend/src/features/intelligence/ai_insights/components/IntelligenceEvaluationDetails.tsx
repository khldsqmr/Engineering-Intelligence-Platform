import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import {
  ShieldCheck,
  Calculator,
  Cpu,
  Info,
} from 'lucide-react'

import { getIntelligenceAudit } from '../../../../services/intelligenceService'

import {
  evaluationCriteria,
  confidenceCriteria,
  calculateWeightedScore,
} from '../../../../utils/intelligenceMethodology'

import type {
  AssessmentCriterion,
} from '../../../../utils/intelligenceMethodology'

import './evaluation.css'

function formatValue(value: number | null | undefined) {
  if (value == null || !Number.isFinite(value)) return 'N/A'

  return new Intl.NumberFormat('en-CA', {
    maximumFractionDigits: 2,
  }).format(value)
}

function formatDuration(value: number | null) {
  return value === null
    ? 'N/A'
    : `${value.toFixed(1)}s`
}

function AssessmentTable({
  criteria,
  scores,
  version,
}: {
  criteria: AssessmentCriterion[]
  scores: Record<string, number>
  version: string
}) {
  const knownVersion = version === '1.0.0'

  return (
    <div className="assessment-table-container">
      {!knownVersion && (
        <p className="assessment-description">
          Weights unavailable for methodology version {version}.
        </p>
      )}

      <table className="assessment-table">
        <thead>
          <tr>
            <th scope="col">Criterion</th>
            <th scope="col">Score / 100</th>
            <th scope="col">Weight</th>
            <th scope="col">Contribution</th>
          </tr>
        </thead>

        <tbody>
          {criteria.map(item => {
            const score = scores[item.key]

            const contribution =
              knownVersion && Number.isFinite(score)
                ? score * item.weight / 100
                : null

            return (
              <tr key={item.key}>
                <th scope="row">
                  <strong>{item.label}</strong>
                  <small>{item.description}</small>
                </th>

                <td>
                  <div className="assessment-score-cell">
                    <strong>{formatValue(score)}</strong>

                    {Number.isFinite(score) && (
                      <div className="assessment-score-track">
                        <span
                          style={{
                            width: `${Math.max(0, Math.min(100, score))}%`,
                          }}
                        />
                      </div>
                    )}
                  </div>
                </td>

                <td>
                  {knownVersion ? `${item.weight}%` : 'N/A'}
                </td>

                <td>{formatValue(contribution)}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

export function IntelligenceEvaluationDetails({
  intelligenceId,
}: {
  intelligenceId: string | null
}) {
  const [expanded, setExpanded] = useState(false)

  const query = useQuery({
    queryKey: ['intelligence-audit', intelligenceId],

    queryFn: ({ signal }) => {
      if (!intelligenceId) {
        throw new Error('Intelligence ID unavailable')
      }

      return getIntelligenceAudit(intelligenceId, signal)
    },

    enabled: expanded && Boolean(intelligenceId),
    staleTime: Infinity,
  })

  const record = query.data

  const approved =
    record?.approvalStatus === 'AUTO_APPROVED'
    && record.auditOnly === false
    && record.intelligenceId === intelligenceId

  const judge = approved
    ? record?.evaluation?.judgeResult
    : null

  const confidence = approved
    ? record?.confidence
    : null

  const uncappedConfidence =
    confidence?.confidenceVersion === '1.0.0'
      ? calculateWeightedScore(
          confidence.dimensions,
          confidenceCriteria,
        )
      : null

  if (!intelligenceId) return null

  return (
    <details
      className="assessment-details"
      onToggle={event =>
        setExpanded(event.currentTarget.open)
      }
    >
      <summary>
        Generation & Evaluation Details
      </summary>

      <div className="assessment-details-content">

        <p className="assessment-description">
          Inspect how this specific intelligence record was
          generated, validated, evaluated and scored.
        </p>

        {query.isPending && (
          <p role="status">Retrieving evaluation details...</p>
        )}

        {query.isError && (
          <div role="alert">
            Unable to retrieve evaluation details.

            <button
              type="button"
              className="assessment-retry"
              onClick={() => void query.refetch()}
            >
              Retry
            </button>
          </div>
        )}

        {record && !approved && (
          <p role="alert">
            This record is not available as approved intelligence.
          </p>
        )}

        {approved && record && (
          <>
            <section className="assessment-section">

              <header className="assessment-section-header">
                <ShieldCheck size={16} />
                <h4>AI Response Evaluation</h4>
                <span className="intelligence-type-label">
                  AI Evaluated
                </span>
              </header>

              <p className="assessment-description">
                The generated response is checked against
                analytical evidence using deterministic validation
                and a separate evaluator model call.
              </p>

              <div className="assessment-validation">
                Deterministic validation:{' '}
                <strong>
                  {record.deterministicValidationPassed
                    ? 'Passed'
                    : 'Not passed'}
                </strong>

                {record.evaluation && (
                  <span>
                    {' · '}
                    {record.evaluation.findings.length}
                    {' validation findings'}
                  </span>
                )}
              </div>

              {judge ? (
                <>
                  <AssessmentTable
                    criteria={evaluationCriteria}
                    scores={judge.scores}
                    version={record.evaluationVersion}
                  />

                  <div className="assessment-total">
                    <span>
                      {record.evaluatorModel === 'deterministic-report'
                        ? 'Deterministic Validation Score'
                        : 'Final Evaluation Score'}
                    </span>
                    <strong>
                      {formatValue(record.evaluationScore)}/100
                    </strong>
                  </div>

                  {record.evaluationVersion === '1.0.0' && (
                    <p className="assessment-description">
                      Approval requires an overall score of at
                      least 85, factual consistency and evidence
                      grounding scores of at least 90, successful
                      deterministic validation and no critical errors.
                    </p>
                  )}

                  <p className="assessment-description">
                    Critical evaluation errors:
                    {' '}{judge.criticalErrors.length}
                  </p>

                  <details className="assessment-nested-details">
                    <summary>Evaluator's reasoning</summary>
                    <p>{judge.explanation}</p>
                    <small>
                      Model-generated assessment, not an
                      independent guarantee of accuracy.
                    </small>
                  </details>
                </>
              ) : (
                <p>Evaluator breakdown unavailable.</p>
              )}

            </section>

            <section className="assessment-section">

              <header className="assessment-section-header">
                <Calculator size={16} />
                <h4>Evidence Confidence</h4>
                <span className="intelligence-type-label">
                  Rule-based
                </span>
              </header>

              <p className="assessment-description">
                Measures evidence strength using deterministic
                rules rather than an AI model's self-reported
                certainty.
              </p>

              {confidence ? (
                <>
                  <AssessmentTable
                    criteria={confidenceCriteria}
                    scores={confidence.dimensions}
                    version={record.confidenceVersion}
                  />

                  <dl className="assessment-metadata">
                    <dt>Uncapped confidence</dt>
                    <dd>{formatValue(uncappedConfidence)}</dd>

                    <dt>Applied confidence cap</dt>
                    <dd>
                      {confidence.appliedCap === null
                        ? 'None'
                        : formatValue(confidence.appliedCap)}
                    </dd>
                  </dl>

                  <div className="assessment-total">
                    <span>Final Evidence Confidence</span>
                    <strong>
                      {formatValue(record.confidenceScore)}/100
                    </strong>
                  </div>

                  {confidence.limitations.length > 0 && (
                    <div className="assessment-limitations">
                      <h5>
                        <Info size={13} />
                        Evidence limitations
                      </h5>

                      <ul>
                        {confidence.limitations.map(
                          (limitation, index) => (
                            <li key={index}>{limitation}</li>
                          ),
                        )}
                      </ul>
                    </div>
                  )}
                </>
              ) : (
                <p>Confidence breakdown unavailable.</p>
              )}

            </section>

            <section className="assessment-section">

              <header className="assessment-section-header">
                <Cpu size={16} />
                <h4>Generation Metadata</h4>
                <span className="intelligence-type-label">
                  System Recorded
                </span>
              </header>

              <p className="assessment-description">
                Operational metadata recorded during
                intelligence generation and evaluation.
              </p>

              <dl className="assessment-metadata">
                <dt>Generator model</dt>
                <dd>{record.generatorModel}</dd>

                <dt>Evaluator model</dt>
                <dd>{record.evaluatorModel ?? 'N/A'}</dd>

                <dt>Generation duration</dt>
                <dd>
                  {formatDuration(record.generationLatencySeconds)}
                </dd>

                <dt>Evaluation duration</dt>
                <dd>
                  {formatDuration(record.evaluatorLatencySeconds)}
                </dd>

                <dt>Generation input tokens</dt>
                <dd>{formatValue(record.generationInputTokens)}</dd>

                <dt>Generation output tokens</dt>
                <dd>{formatValue(record.generationOutputTokens)}</dd>

                <dt>Generator prompt version</dt>
                <dd>{record.generatorPromptVersion}</dd>

                <dt>Evaluator prompt version</dt>
                <dd>{record.evaluatorPromptVersion ?? 'N/A'}</dd>

                <dt>Evaluation methodology version</dt>
                <dd>{record.evaluationVersion}</dd>

                <dt>Confidence methodology version</dt>
                <dd>{record.confidenceVersion}</dd>

                <dt>Historical insights reused</dt>
                <dd>{record.historicalIntelligenceIds.length}</dd>

                <dt>Eligible for future historical context</dt>
                <dd>
                  {record.eligibleForHistoricalContext
                    ? 'Yes'
                    : 'No'}
                </dd>

                <dt>Generated at</dt>
                <dd>
                  {new Date(record.createdAt).toLocaleString(
                    'en-CA',
                    { timeZone: 'UTC' },
                  )} UTC
                </dd>

                <dt>Intelligence ID</dt>
                <dd className="assessment-record-id">
                  {record.intelligenceId}
                </dd>
              </dl>

              {record.generatorModel === record.evaluatorModel && (
                <p className="assessment-description">
                  Generation and evaluation use the same model
                  in separate calls. The evaluation is not fully
                  independent and may share the generator's biases.
                </p>
              )}

            </section>
          </>
        )}

      </div>
    </details>
  )
}
