import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import {
  History,
  Archive,
  ArrowLeft,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  ArrowRight,
} from 'lucide-react'

import { PageHeader } from '../../../components/layout/PageHeader'

import {
  getIntelligenceHistory,
} from '../../../services/intelligenceService'

import {
  HistoryRecordInspector,
} from './components/HistoryRecordInspector'

import './components/history.css'

const PAGE_SIZE = 10

function formatPeriod(start: string, end: string) {
  const last = new Date(`${end.slice(0, 10)}T00:00:00Z`)
  last.setUTCDate(last.getUTCDate() - 1)

  return `${start.slice(0, 10)} to ${last.toISOString().slice(0, 10)}`
}

function formatCreatedAt(value: string) {
  return new Date(value).toLocaleString('en-CA', {
    timeZone: 'UTC',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  })
}

export function IntelligenceHistoryPage() {
  const [offset, setOffset] = useState(0)
  const [showArchive, setShowArchive] = useState(false)

  const [selectedId, setSelectedId] =
    useState<string | null>(null)

  useEffect(() => {
    if (!selectedId) return

    const inspector = document.getElementById(
      'history-record-inspector',
    )

    inspector?.scrollIntoView({
      behavior: window.matchMedia(
        '(prefers-reduced-motion: reduce)',
      ).matches ? 'instant' : 'smooth',
      block: 'start',
    })
  }, [selectedId])


  const query = useQuery({
    queryKey: ['intelligence-history', 'library'],

    queryFn: async ({ signal }) => {
      const first = await getIntelligenceHistory(100, 0, signal)
      const records = [...first.records]

      while (records.length < first.total) {
        const next = await getIntelligenceHistory(
          100,
          records.length,
          signal,
        )

        if (next.records.length === 0) break

        records.push(...next.records)
      }

      return {
        ...first,
        records: Array.from(
          new Map(
            records.map(record => [
              record.intelligenceId,
              record,
            ]),
          ).values(),
        ),
      }
    },

    staleTime: 0,
  })

  const filteredRecords = query.data?.records.filter(
    record => showArchive
      ? record.approvalStatus !== 'AUTO_APPROVED'
      : record.approvalStatus === 'AUTO_APPROVED',
  ) ?? []

  const data = query.data
    ? {
        ...query.data,
        total: filteredRecords.length,
        records: filteredRecords.slice(
          offset,
          offset + PAGE_SIZE,
        ),
      }
    : undefined

  function toggleArchive() {
    setSelectedId(null)
    setOffset(0)
    setShowArchive(current => !current)
  }

  function changePage(nextOffset: number) {
    setSelectedId(null)
    setOffset(nextOffset)
  }

  return (
    <section className="workspace-page">

      <PageHeader
        category="Intelligence"
        title="Intelligence History"
        description="Explore previously generated intelligence, approval decisions and the information retained for future analysis."
      />

      <section className="history-card">

        <header className="history-card-header">
          <div>
            <h2>
              {showArchive
                ? <Archive size={17} />
                : <History size={17} />}
              {showArchive
                ? 'Generation Archive'
                : 'Approved Intelligence'}
            </h2>

            <p>
              {showArchive
                ? 'Unapproved generation attempts retained for audit and diagnostics.'
                : 'Previously approved intelligence across all reporting periods.'}
            </p>
          </div>

          <button
            type="button"
            className="history-control"
            disabled={query.isFetching}
            onClick={() => void query.refetch()}
          >
            <RefreshCw size={13} />
            Refresh
          </button>
        </header>

        {query.isPending ? (
          <p role="status">Loading intelligence history...</p>
        ) : query.isError || !data ? (
          <div role="alert">
            Unable to retrieve intelligence history.

            <button
              type="button"
              className="history-control"
              onClick={() => void query.refetch()}
            >
              Retry
            </button>
          </div>
        ) : (
          <>
            <div className="history-summary">
              {data.repository}
              {' · '}
              {data.total} {showArchive
                ? 'archived'
                : 'approved'} records
              {' · '}
              All reporting periods
            </div>

            {data.records.length === 0 ? (
              <div className="history-empty">
                {showArchive
                  ? 'No archived generation attempts.'
                  : 'No approved intelligence on this page. Generate a narrative in AI Insights to build intelligence history.'}
              </div>
            ) : (
              <div className="history-table-scroll">
                <table className="history-table">
                  <thead>
                    <tr>
                      <th scope="col">Reporting Period</th>
                      <th scope="col">Generated (UTC)</th>
                      <th scope="col">Decision</th>
                      <th scope="col">Quality</th>
                      <th scope="col">Confidence</th>
                      <th scope="col">Reuse Eligible</th>
                      <th scope="col">Details</th>
                    </tr>
                  </thead>

                  <tbody>
                    {data.records.map(record => (
                      <tr
                        key={record.intelligenceId}
                        data-selected={
                          selectedId === record.intelligenceId
                        }
                      >
                        <th scope="row">
                          {formatPeriod(
                            record.periodStart,
                            record.periodEndExclusive,
                          )}
                        </th>

                        <td>{formatCreatedAt(record.createdAt)}</td>

                        <td>
                          <span
                            className="history-status"
                            data-status={record.approvalStatus}
                          >
                            {record.approvalStatus.replaceAll('_', ' ')}
                          </span>
                        </td>

                        <td className="history-numeric">
                          {record.evaluationScore ?? 'N/A'}
                        </td>

                        <td className="history-numeric">
                          {record.confidenceScore ?? 'N/A'}
                        </td>

                        <td>
                          {record.eligibleForHistoricalContext
                            ? 'Yes'
                            : 'No'}
                        </td>

                        <td>
                          <button
                            type="button"
                            className="history-view-button"
                            aria-expanded={
                              selectedId === record.intelligenceId
                            }
                            onClick={() => setSelectedId(
                              selectedId === record.intelligenceId
                                ? null
                                : record.intelligenceId,
                            )}
                          >
                            {selectedId === record.intelligenceId
                              ? 'Selected'
                              : 'Explore'}

                            <ArrowRight size={12} />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            <footer className="history-pagination">
              <span>
                {data.records.length
                  ? `${offset + 1}–${offset + data.records.length} of ${data.total}`
                  : `${data.total} records`}
              </span>

              <div>
                <button
                  type="button"
                  className="history-control"
                  disabled={offset === 0}
                  aria-label="Previous history page"
                  onClick={() => changePage(
                    Math.max(0, offset - PAGE_SIZE),
                  )}
                >
                  <ChevronLeft size={14} />
                </button>

                <button
                  type="button"
                  className="history-control"
                  disabled={offset + PAGE_SIZE >= data.total}
                  aria-label="Next history page"
                  onClick={() => changePage(offset + PAGE_SIZE)}
                >
                  <ChevronRight size={14} />
                </button>
              </div>
            </footer>
          </>
        )}

        <div className="history-archive-navigation">
          <button
            type="button"
            className="history-archive-link"
            onClick={toggleArchive}
          >
            {showArchive
              ? <ArrowLeft size={13} />
              : <Archive size={13} />}
            {showArchive
              ? 'Back to approved intelligence'
              : 'View generation archive'}
          </button>
        </div>

      </section>

      {selectedId && (
        <HistoryRecordInspector
          key={selectedId}
          intelligenceId={selectedId}
          onClose={() => setSelectedId(null)}
        />
      )}

    </section>
  )
}
