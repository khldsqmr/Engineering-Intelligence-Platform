import { useQuery } from '@tanstack/react-query'
import { X, Database, Info } from 'lucide-react'

import {
  getIntelligenceHistoryDetail,
} from '../../../../services/intelligenceService'

import {
  IntelligenceEvaluationDetails,
} from '../../ai_insights/components/IntelligenceEvaluationDetails'

function TechnicalDetails({
  title,
  description,
  value,
}: {
  title: string
  description: string
  value: unknown
}) {
  return (
    <details className="history-technical-details">
      <summary>{title}</summary>

      <p>{description}</p>

      <pre>{JSON.stringify(value ?? null, null, 2)}</pre>
    </details>
  )
}

export function HistoryRecordInspector({
  intelligenceId,
  onClose,
}: {
  intelligenceId: string
  onClose: () => void
}) {
  const query = useQuery({
    queryKey: ['intelligence-audit', intelligenceId],

    queryFn: ({ signal }) =>
      getIntelligenceHistoryDetail(intelligenceId, signal),

    staleTime: Infinity,
  })

  const record = query.data

  const approved =
    record?.approvalStatus === 'AUTO_APPROVED' &&
    record.auditOnly === false

  return (
    <section
      className="history-inspector"
      id="history-record-inspector"
    >

      <header className="history-inspector-header">
        <div>
          <small>EXPLORING · SAVED INTELLIGENCE</small>
          <h2>Intelligence Record</h2>

          <span>
            <Database size={11} />
            Intelligence History Store
          </span>
        </div>

        <button
          type="button"
          className="history-control"
          aria-label="Close intelligence record"
          onClick={onClose}
        >
          <X size={16} />
        </button>
      </header>

      {query.isPending ? (
        <p role="status">Retrieving saved intelligence...</p>
      ) : query.isError || !record ? (
        <div role="alert">
          Unable to retrieve the intelligence record.

          <button
            type="button"
            className="history-control"
            onClick={() => void query.refetch()}
          >
            Retry
          </button>
        </div>
      ) : record.intelligenceId !== intelligenceId ? (
        <p role="alert">Intelligence record mismatch.</p>
      ) : (
        <>
          <div className="history-record-metadata">
            <div>
              <small>Approval decision</small>

              <strong>
                {record.approvalStatus.replaceAll('_', ' ')}
              </strong>
            </div>

            <div>
              <small>
                {record.evaluatorModel === 'deterministic-report'
                  ? 'Report Validation'
                  : 'AI Response Quality'}
              </small>
              <strong>{record.evaluatorModel === 'deterministic-report'
                ? 'Passed'
                : (record.evaluationScore ?? 'N/A')}</strong>
            </div>

            <div>
              <small>Heuristic Confidence</small>
              <strong>{record.confidenceScore ?? 'N/A'}</strong>
            </div>

            <div>
              <small>Eligible for reuse</small>

              <strong>
                {record.eligibleForHistoricalContext
                  ? 'Yes'
                  : 'No'}
              </strong>
            </div>
          </div>

          <section className="history-narrative-section">
            <h3>Interaction Type</h3>

            <p>
              {record.intelligenceMode === 'question'
                ? 'Copilot · AI Reasoning'
                : 'Proactive Intelligence Narrative'}
            </p>

            {record.question && (
              <>
                <h3>Original Question</h3>
                <p>{record.question}</p>
              </>
            )}
          </section>

          {!approved && (
            <div className="history-audit-notice">
              <Info size={16} />

              <span>
                This response is retained for audit purposes.
                It is not published as approved intelligence
                or eligible for historical reuse.
              </span>
            </div>
          )}

          {record.manualReview && (
            <section className="history-narrative-section">
              <h3>Manual Governance Review</h3>

              <p>{record.manualReview.reason}</p>

              <p>
                Original decision: {record.originalApprovalStatus}
              </p>

              <small>
                The original model evaluation is preserved for audit.
                This intelligence has been withdrawn from publication
                and historical reuse.
              </small>
            </section>
          )}

          {approved && (
            <>
              {typeof record.narrative === 'string' && (
                <section className="history-narrative-section">
                  <h3>
                    {record.intelligenceMode === 'question'
                      ? 'Saved Copilot Answer'
                      : 'Saved Performance Observation'}
                  </h3>
                  <p>{record.narrative}</p>
                </section>
              )}

              {typeof record.hypothesis === 'string' && (
                <section className="history-narrative-section">
                  <h3>Saved Root-Cause Hypothesis</h3>
                  <p>{record.hypothesis}</p>

                  <small>
                    Potential explanation, not a confirmed cause.
                  </small>
                </section>
              )}

              <IntelligenceEvaluationDetails
                intelligenceId={record.intelligenceId}
              />
            </>
          )}

          <section className="history-narrative-section">
            <h3>Historical Intelligence Reuse</h3>

            <p>
              {record.historicalIntelligenceIds.length
                ? `${record.historicalIntelligenceIds.length} earlier intelligence records contributed to this generation.`
                : 'No previous intelligence records were used during this generation.'}
            </p>

            <p>
              {approved && record.eligibleForHistoricalContext
                ? 'This record is eligible for consideration in future reporting periods, subject to compatibility and retrieval rules.'
                : 'This record is not eligible for historical reuse.'}
            </p>

            {record.historicalIntelligenceIds.length > 0 && (
              <TechnicalDetails
                title="Historical intelligence references"
                description="Identifiers of previous intelligence records supplied to this generation."
                value={record.historicalIntelligenceIds}
              />
            )}
          </section>

          <TechnicalDetails
            title="Numerical grounding and evaluation audit"
            description="Recorded evaluation findings and original numerical template, when available."
            value={record.evaluation}
          />

          <section className="history-narrative-section">
            <h3>Original Generation Artifacts</h3>

            <p>
              Inspect the exact saved information associated with
              this generation, rather than today's assembled context.
            </p>
          </section>

          <TechnicalDetails
            title="Saved context snapshot"
            description="The complete structured context retained for this generation."
            value={record.context}
          />

          <TechnicalDetails
            title="Model input"
            description="The projected input recorded for the language model."
            value={record.modelInput}
          />

          <TechnicalDetails
            title={approved
              ? 'Structured AI response'
              : 'Unapproved response · Audit only'}
            description={approved
              ? 'The structured response produced by the generator.'
              : 'Unapproved model output retained for diagnostic purposes. Do not treat it as established findings.'}
            value={record.response}
          />

          {!approved && (
            <>
              <TechnicalDetails
                title="Validation and evaluation results"
                description="Recorded findings and assessment associated with the unapproved response."
                value={record.evaluation}
              />

              <TechnicalDetails
                title="Confidence assessment"
                description="Recorded evidence-strength assessment, when available."
                value={record.confidence}
              />
            </>
          )}

          <TechnicalDetails
            title="Record metadata"
            description="Identifiers and versions retained for traceability."
            value={{
              intelligenceId: record.intelligenceId,
              ingestionRunId: record.ingestionRunId,
              repository: record.repository,
              contextVersion: record.contextVersion,
              metricVersions: record.metricVersions,
              generatorModel: record.generatorModel,
              evaluatorModel: record.evaluatorModel,
              createdAt: record.createdAt,
            }}
          />
        </>
      )}

    </section>
  )
}
