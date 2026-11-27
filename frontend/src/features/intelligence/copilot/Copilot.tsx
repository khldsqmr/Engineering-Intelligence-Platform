import { useEffect, useRef, useState } from 'react'

import {
  Bot,
  ChevronDown,
  LoaderCircle,
  MessageCircle,
  Send,
  Sparkles,
  Trash2,
  X,
} from 'lucide-react'

import {
  useCopilot,
  type CopilotTurn,
} from './useCopilot'

import type {
  IntelligenceEvidence,
} from '../../../types/intelligence'

import './copilot.css'

const suggestions = [
  "Summarize this week's engineering performance.",
  'What could explain changes in median merge duration?',
  'How does review performance compare with historical benchmarks?',
  'Which metrics require further investigation?',
]

function formatValue(
  value: number | null,
  unit: string,
) {
  if (value === null) return 'N/A'

  const number = new Intl.NumberFormat('en-US', {
    maximumFractionDigits: 2,
  }).format(value)

  const suffix: Record<string, string> = {
    HOURS: ' hrs',
    PERCENT: '%',
    LINES: ' lines',
    FILES: ' files',
  }

  return number + (suffix[unit] ?? '')
}

function EvidenceCard({
  evidence,
  expanded = false,
}: {
  evidence: IntelligenceEvidence
  expanded?: boolean
}) {
  const semantic = evidence.semanticContext
  const unit = semantic?.metricUnit ?? ''

  return (
    <details className="copilot-evidence" open={expanded}>

      <summary>
        <span className="copilot-evidence-ref">
          {evidence.evidenceRef}
        </span>

        <span>
          {semantic?.metricName ?? evidence.metricId}
        </span>

        <ChevronDown size={13} />
      </summary>

      <div className="copilot-evidence-body">

        <div className="copilot-evidence-values">
          <div>
            <span>Current</span>
            <strong title={String(evidence.currentValue ?? 'N/A')}>
              {formatValue(evidence.currentValue, unit)}
            </strong>
          </div>

          <div>
            <span>Previous</span>
            <strong title={String(evidence.previousValue ?? 'N/A')}>
              {formatValue(evidence.previousValue, unit)}
            </strong>
          </div>
        </div>

        <p>{semantic?.metricDescription}</p>

        <p>{semantic?.calculationDefinition}</p>

        <dl className="copilot-evidence-metadata">
          <div>
            <dt>Direction</dt>
            <dd>{evidence.direction}</dd>
          </div>

          <div>
            <dt>Sample size</dt>
            <dd>{evidence.sampleSize ?? 'N/A'}</dd>
          </div>

          <div>
            <dt>Coverage</dt>
            <dd>{evidence.coverageStatus}</dd>
          </div>

          <div>
            <dt>Metric version</dt>
            <dd>{evidence.metricVersion}</dd>
          </div>
        </dl>

        <small className="copilot-evidence-id">
          Evidence ID: {evidence.evidenceId}
        </small>

      </div>
    </details>
  )
}

function CopilotMessage({ turn }: { turn: CopilotTurn }) {
  const result = turn.result

  const approved =
    result?.status === 'AUTO_APPROVED' &&
    result.response?.status === 'ANSWERED'

  const output = approved ? result.response : null

  return (
    <article className="copilot-turn">

      <div className="copilot-user-message">
        {turn.question}
      </div>

      <div className="copilot-message-context">
        {turn.repository} · {turn.period.periodStart}
        {' to '}
        {turn.period.periodEndExclusive} (exclusive)
      </div>

      <div className="copilot-assistant-message">

        <div className="copilot-assistant-label">
          <Sparkles size={14} />
          <strong>EIP Copilot</strong>
        </div>

        {turn.error ? (
          <div className="copilot-notice">
            <strong>Unable to complete the request</strong>
            <p>{turn.error}</p>
            <p>You can try submitting the question again.</p>
          </div>
        ) : !result ? (
          <div className="copilot-thinking" role="status">
            <LoaderCircle size={16} />
            <span>Processing your request...</span>
          </div>
        ) : result.status === 'INSUFFICIENT_EVIDENCE' ? (
          <div className="copilot-notice">
            The available evidence is insufficient to answer
            this question reliably.
          </div>
        ) : result.status === 'CHAT_ANSWERED' ? (
          <p>{result.chatAnswer}</p>
        ) : result.status === 'FACT_ANSWERED' ? (
          <>
            <div className="copilot-fact-label">
              Gold Analytical Layer · Fact
            </div>

            <p className="copilot-fact-answer">{result.factAnswer}</p>

            <section className="copilot-evidence-list">
              <h4>Supporting analytical evidence</h4>

              {result.evidence.map(evidence => (
                <EvidenceCard
                  key={evidence.evidenceId}
                  evidence={evidence}
                />
              ))}
            </section>

            <small className="copilot-disclaimer">
              {result.plannerStatus === 'VALIDATED'
                ? 'AI-assisted intent recognition. Numerical values retrieved directly from governed analytical evidence.'
                : 'Deterministically retrieved from governed analytical evidence. No AI inference performed.'}
            </small>
          </>
        ) : !approved && result.factFallback ? (
          <>
            <div className="copilot-notice">
              <strong>AI interpretation unavailable</strong>
              <p>{result.factFallback}</p>
              <small>Status: {result.status}</small>
            </div>

            <div className="copilot-fact-label">
              Gold Analytical Layer · Fact
            </div>

            <section className="copilot-evidence-list">
              <h4>Available analytical facts</h4>

              {result.evidence.map(evidence => (
                <EvidenceCard
                  key={evidence.evidenceId}
                  evidence={evidence}
                  expanded
                />
              ))}
            </section>

            <small className="copilot-disclaimer">
              These facts are retrieved independently from
              governed analytical evidence. They do not establish
              causation. Unvalidated AI interpretation is withheld.
            </small>
          </>
        ) : !approved || !output ? (
          <div className="copilot-notice">
            <strong>Response not published</strong>
            <p>
              The generated answer did not satisfy the
              required intelligence safeguards.
            </p>
            <small>Status: {result.status}</small>
          </div>
        ) : (
          <>
            <div className="copilot-answer">

              {output.narrative && (
                <section>
                  <h4>Observation</h4>
                  <p>{output.narrative.text}</p>

                  <small>
                    Evidence:{' '}
                    {output.narrative.supportingEvidence
                      .map(item => item.evidenceRef)
                      .join(', ')}
                  </small>
                </section>
              )}

              {output.hypothesis && (
                <section>
                  <h4>Possible explanation</h4>
                  <p>{output.hypothesis.text}</p>

                  <small>
                    Supporting evidence:{' '}
                    {output.hypothesis.supportingEvidence
                      .map(item => item.evidenceRef)
                      .join(', ')}
                  </small>

                  {output.hypothesis.counterEvidence.length > 0 && (
                    <small>
                      Counter-evidence:{' '}
                      {output.hypothesis.counterEvidence
                        .map(item => item.evidenceRef)
                        .join(', ')}
                    </small>
                  )}
                </section>
              )}

              {output.alternativeExplanations.length > 0 && (
                <section>
                  <h4>Alternative explanations</h4>

                  <ul>
                    {output.alternativeExplanations.map((item, index) => (
                      <li key={index}>{item}</li>
                    ))}
                  </ul>
                </section>
              )}

              {output.recommendedInvestigation && (
                <section>
                  <h4>Recommended investigation</h4>
                  <p>{output.recommendedInvestigation}</p>
                </section>
              )}

            </div>

            <div className="copilot-assessment">

              <div>
                <span>AI quality</span>
                <strong>
                  {result.evaluationScore ?? 'N/A'}
                  {result.evaluationScore !== null ? '/100' : ''}
                </strong>
              </div>

              <div>
                <span>Evidence confidence</span>
                <strong>
                  {result.confidenceScore ?? 'N/A'}
                  {result.confidenceScore !== null ? '/100' : ''}
                </strong>
              </div>

            </div>

            {result.evidence.length > 0 && (
              <section className="copilot-evidence-list">

                <h4>Supporting analytical evidence</h4>

                {result.evidence.map(evidence => (
                  <EvidenceCard
                    key={evidence.evidenceId}
                    evidence={evidence}
                  />
                ))}

              </section>
            )}

            <small className="copilot-disclaimer">
              AI-generated interpretation. Automated evaluation
              does not guarantee factual correctness.
              Confidence is not a causal probability.
            </small>

          </>
        )}

      </div>

    </article>
  )
}

export function Copilot() {
  const [open, setOpen] = useState(false)
  const [draft, setDraft] = useState('')

  const chat = useCopilot()

  const messagesRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const launcherRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    if (open && messagesRef.current) {
      messagesRef.current.scrollTop =
        messagesRef.current.scrollHeight
    }
  }, [open, chat.turns, chat.pending])

  useEffect(() => {
    if (open) inputRef.current?.focus()
  }, [open])

  function close() {
    setOpen(false)
    requestAnimationFrame(() => launcherRef.current?.focus())
  }

  function send(question: string) {
    if (!chat.ready || chat.pending || !question.trim()) return

    void chat.submit(question)
    setDraft('')
  }

  return (
    <div className="copilot-root">

      {open && (
        <section
          className="copilot-panel"
          id="eip-copilot-panel"
          aria-label="EIP Copilot"
          onKeyDown={event => {
            if (event.key === 'Escape') close()
          }}
        >

          <header className="copilot-header">

            <div className="copilot-avatar">
              <Bot size={23} />
            </div>

            <div className="copilot-header-title">
              <strong>EIP Copilot</strong>
              <span>Engineering intelligence assistant</span>
            </div>

            <button
              type="button"
              title="Clear conversation"
              aria-label="Clear conversation"
              disabled={chat.pending || chat.turns.length === 0}
              onClick={chat.clear}
            >
              <Trash2 size={16} />
            </button>

            <button
              type="button"
              aria-label="Close Copilot"
              title="Close Copilot"
              onClick={close}
            >
              <X size={19} />
            </button>

          </header>

          <div className="copilot-context">

            <span>Active analytical context</span>

            <strong>
              {chat.ready ? chat.repository : 'Context unavailable'}
            </strong>

            {chat.ready && chat.period && (
              <small>
                {chat.period.periodStart} to{' '}
                {chat.period.periodEndExclusive} (exclusive) · UTC
              </small>
            )}

          </div>

          <div
            className="copilot-messages"
            ref={messagesRef}
            role="log"
            aria-label="Copilot conversation"
          >

            {chat.turns.length === 0 ? (
              <div className="copilot-welcome">

                <div className="copilot-welcome-icon">
                  <Sparkles size={25} />
                </div>

                <h3>How can I help?</h3>

                <p>
                  Ask questions about engineering performance,
                  review engagement and historical trends.
                </p>

                <div className="copilot-suggestions">

                  {suggestions.map(question => (
                    <button
                      type="button"
                      key={question}
                      disabled={!chat.ready || chat.pending}
                      onClick={() => send(question)}
                    >
                      {question}
                    </button>
                  ))}

                </div>

              </div>
            ) : (
              chat.turns.map(turn => (
                <CopilotMessage key={turn.id} turn={turn} />
              ))
            )}

          </div>

          <form
            className="copilot-composer"
            onSubmit={event => {
              event.preventDefault()
              send(draft)
            }}
          >

            <div className="copilot-input-row">

              <textarea
                ref={inputRef}
                value={draft}
                maxLength={500}
                rows={2}
                placeholder="Ask Copilot..."
                aria-label="Ask Copilot a question"
                onChange={event => setDraft(event.target.value)}
                onKeyDown={event => {
                  if (
                    event.key === 'Enter' &&
                    !event.shiftKey &&
                    !event.nativeEvent.isComposing
                  ) {
                    event.preventDefault()
                    send(draft)
                  }
                }}
              />

              <button
                type="submit"
                aria-label="Send question"
                disabled={
                  !chat.ready ||
                  chat.pending ||
                  !draft.trim()
                }
              >
                <Send size={17} />
              </button>

            </div>

            <div className="copilot-composer-meta">
              <span>Remembers up to 3 recent question topics.</span>
              <span>{draft.length}/500</span>
            </div>

            <small className="copilot-footer">
              Governed analytical facts · Validated AI interpretation
            </small>

          </form>

        </section>
      )}

      {!open && (
        <button
          ref={launcherRef}
          type="button"
          className="copilot-launcher"
          aria-label="Open Copilot"
          aria-expanded={false}
          onClick={() => setOpen(true)}
        >
          <MessageCircle size={20} />
          <span>Ask Copilot</span>
        </button>
      )}

    </div>
  )
}
