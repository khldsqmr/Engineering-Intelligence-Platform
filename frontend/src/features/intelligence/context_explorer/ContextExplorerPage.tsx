import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { RefreshCw } from 'lucide-react'

import { PageHeader } from '../../../components/layout/PageHeader'
import { ReportingPeriodFilter } from '../../../components/filters/ReportingPeriodFilter'

import { useReportingWeek } from '../../../hooks/useReportingWeek'
import { getIntelligenceContext } from '../../../services/intelligenceService'

import type { InsightsResponse } from '../../../types/analytics'

import {
  ContextArchitecture,
} from './components/ContextArchitecture'

import type {
  ContextNode,
} from './components/ContextArchitecture'

import { ContextInspector } from './components/ContextInspector'

import './components/context.css'

function ContextWorkspace({
  analytics,
}: {
  analytics: InsightsResponse
}) {
  const [selected, setSelected] =
    useState<ContextNode>('assembly')

  const query = useQuery({
    queryKey: [
      'intelligence-context',
      analytics.repository,
      analytics.ingestionRunId,
      analytics.periodStart,
      analytics.periodEndExclusive,
    ],

    queryFn: ({ signal }) =>
      getIntelligenceContext(
        {
          periodStart: analytics.periodStart,
          periodEndExclusive: analytics.periodEndExclusive,
        },
        signal,
      ),
  })

  if (query.isPending) {
    return (
      <div className="empty-state" role="status">
        Assembling analytical context...
      </div>
    )
  }

  if (query.isError || !query.data) {
    return (
      <div className="empty-state">
        <h2>Unable to retrieve intelligence context</h2>

        <button
          type="button"
          className="primary-button"
          onClick={() => void query.refetch()}
        >
          Retry
        </button>
      </div>
    )
  }

  const context = query.data

  if (
    context.repository !== analytics.repository ||
    context.ingestionRunId !== analytics.ingestionRunId ||
    context.temporalContext.periodStart.slice(0, 10) !==
      analytics.periodStart.slice(0, 10) ||
    context.temporalContext.periodEndExclusive.slice(0, 10) !==
      analytics.periodEndExclusive.slice(0, 10)
  ) {
    return (
      <div className="empty-state" role="alert">
        Context does not match the selected analytical snapshot.
        Refresh the application before continuing.
      </div>
    )
  }

  return (
    <>
      <div className="context-refresh-bar">
        <span className="context-footnote">
          Context v{context.contextVersion}
          {' · '}
          {context.repository}
          {' · '}
          Current assembled context
        </span>

        <button
          type="button"
          className="context-refresh-button"
          disabled={query.isFetching}
          onClick={() => void query.refetch()}
        >
          <RefreshCw size={12} />
          {query.isFetching ? 'Refreshing...' : 'Refresh context'}
        </button>
      </div>

      <div className="context-workspace-grid">

        <ContextArchitecture
          context={context}
          selected={selected}
          onSelect={setSelected}
        />

        <ContextInspector
          key={selected}
          context={context}
          selected={selected}
        />

      </div>

      <details className="context-detail">
        <summary>Technical context payload</summary>

        <div className="context-detail-body">
          <p className="context-footnote">
            Assembled context returned by the backend.
            This is not necessarily the exact projected prompt
            used by a previously generated narrative.
          </p>

          <pre style={{
            overflow: 'auto',
            maxHeight: '400px',
            fontSize: '11px',
            padding: '12px',
            background: 'var(--color-surface-secondary)',
          }}>
            {JSON.stringify(context, null, 2)}
          </pre>
        </div>
      </details>

    </>
  )
}

export function ContextExplorerPage() {
  const week = useReportingWeek()

  const {
    data,
    isPending,
    isError,
    refetch,
  } = week.query

  return (
    <section className="workspace-page">

      <PageHeader
        category="Intelligence"
        title="Context Explorer"
        description="Understand how engineering data becomes AI intelligence, and how approved insights inform future analysis."
      />

      <ReportingPeriodFilter week={week} />

      {isPending ? (
        <div className="empty-state" role="status">
          Loading analytical context...
        </div>
      ) : isError || !data ? (
        <div className="empty-state">
          <h2>Unable to load analytical data</h2>

          <button
            type="button"
            className="primary-button"
            onClick={() => void refetch()}
          >
            Retry
          </button>
        </div>
      ) : (
        <ContextWorkspace
          key={`${data.ingestionRunId}:${data.periodStart}:${data.periodEndExclusive}`}
          analytics={data}
        />
      )}

    </section>
  )
}
