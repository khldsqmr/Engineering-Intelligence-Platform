import { useRef, useState } from 'react'

import { useReportingWeek } from '../../../hooks/useReportingWeek'

import {
  askCopilot,
  type CopilotResponse,
} from '../../../services/copilotService'

import type { ReportingPeriod } from '../../../types/analytics'

export interface CopilotTurn {
  id: number
  question: string
  repository: string
  ingestionRunId: string
  period: ReportingPeriod
  result?: CopilotResponse
  error?: string
}

export function useCopilot() {
  const week = useReportingWeek()

  const [turns, setTurns] = useState<CopilotTurn[]>([])
  const [pending, setPending] = useState(false)

  const busy = useRef(false)
  const sequence = useRef(0)

  const period = week.period
  const analytics = week.query.data

  const ready = Boolean(
    period &&
    analytics &&
    week.latestData &&
    !week.query.isError &&
    analytics.repository === week.latestData.repository &&
    analytics.ingestionRunId === week.latestData.ingestionRunId &&
    analytics.periodStart === period.periodStart &&
    analytics.periodEndExclusive === period.periodEndExclusive,
  )

  async function submit(question: string) {
    const text = question.trim()

    if (
      !ready ||
      !period ||
      !analytics ||
      !text ||
      text.length > 500 ||
      busy.current
    ) return

    busy.current = true
    setPending(true)

    const turn: CopilotTurn = {
      id: ++sequence.current,
      question: text,
      repository: analytics.repository,
      ingestionRunId: analytics.ingestionRunId,
      period: {
        periodStart: period.periodStart,
        periodEndExclusive: period.periodEndExclusive,
      },
    }

    const previousQuestions = turns
      .filter(item =>
        item.repository === turn.repository &&
        item.ingestionRunId === turn.ingestionRunId &&
        item.period.periodStart === turn.period.periodStart &&
        item.period.periodEndExclusive === turn.period.periodEndExclusive &&
        (
          item.result?.status === 'CHAT_ANSWERED' ||
          item.result?.status === 'FACT_ANSWERED'
        )
      )
      .slice(-3)
      .map(item => item.question)

    setTurns(current => [...current, turn])

    try {
      const result = await askCopilot(
        text,
        turn.period,
        previousQuestions,
      )

      if (
        result.repository !== turn.repository ||
        result.periodStart !== turn.period.periodStart ||
        result.periodEndExclusive !== turn.period.periodEndExclusive
      ) {
        throw new Error('Response context mismatch.')
      }

      setTurns(current =>
        current.map(item =>
          item.id === turn.id
            ? { ...item, result }
            : item,
        ),
      )
    } catch (error) {
      setTurns(current =>
        current.map(item =>
          item.id === turn.id
            ? {
                ...item,
                error: error instanceof Error
                  ? error.message
                  : 'Copilot request failed.',
              }
            : item,
        ),
      )
    } finally {
      busy.current = false
      setPending(false)
    }
  }

  function clear() {
    if (!busy.current) {
      setTurns([])
    }
  }

  return {
    turns,
    pending,
    ready,
    period,
    repository: analytics?.repository,
    submit,
    clear,
  }
}
