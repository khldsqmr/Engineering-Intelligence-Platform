import { useState } from 'react'

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { ChartCard } from './ChartCard'

import type {
  AnalyticalMetric,
  MetricUnit,
} from '../../types/analytics'

import type {
  DailyInsight,
} from '../../hooks/useDailyInsights'

import {
  findMetric,
  formatMetricValue,
  formatMetricChange,
  formatNumber,
  getChangeTone,
} from '../../utils/metricFormatting'

import './metric-trend.css'

interface MetricTrendChartProps {
  metrics: AnalyticalMetric[]
  days: DailyInsight[]
  isLoading: boolean
  hasErrors: boolean
  onRetry: () => void
}

const unitLabels: Record<MetricUnit, string> = {
  COUNT: 'Count',
  HOURS: 'Hours',
  PERCENT: 'Percentage (%)',
  LINES: 'Lines',
  FILES: 'Files',
}

const dayStateLabels = {
  ACTUAL: 'Observed actuals',
  LOADING: 'Loading',
  NOT_AVAILABLE: 'Not available',
  PENDING: 'Awaiting data',
  ERROR: 'Retrieval failed',
}

function formatDay(date: string) {
  return new Intl.DateTimeFormat('en-CA', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    timeZone: 'UTC',
  }).format(new Date(date))
}

function dailyMetric(
  day: DailyInsight,
  metricId: string,
) {
  return findMetric(
    day.data?.metrics ?? [],
    metricId,
  )
}

function axisScale(
  unit: MetricUnit,
  values: Array<number | null>,
): {
  domain: [number, number]
  ticks: number[]
} {
  const valid = values.filter(
    (value): value is number =>
      value !== null && Number.isFinite(value),
  )

  const intervals = 4

  if (!valid.length) {
    return unit === 'PERCENT'
      ? {
          domain: [0, 100],
          ticks: [0, 25, 50, 75, 100],
        }
      : {
          domain: [0, 4],
          ticks: [0, 1, 2, 3, 4],
        }
  }

  const minimum = Math.min(...valid)
  const maximum = Math.max(...valid)
  const range = maximum - minimum

  const padding = range > 0
    ? range * 0.08
    : Math.max(maximum * 0.05, 0.1)

  const low = Math.max(0, minimum - padding)

  const high = unit === 'PERCENT'
    ? Math.min(100, maximum + padding)
    : maximum + padding

  const targetStep = Math.max(
    (high - low) / intervals,
    unit === 'COUNT' ? 1 : 0.000001,
  )

  const exponent = Math.floor(
    Math.log10(targetStep),
  )

  const candidates = []

  for (
    let power = exponent - 1;
    power <= exponent + 3;
    power++
  ) {
    for (const factor of [1, 2, 2.5, 5, 7.5]) {
      candidates.push(factor * 10 ** power)
    }
  }

  if (unit === 'PERCENT') {
    candidates.push(25)
  }

  candidates.sort((a, b) => a - b)

  const clean = (value: number) =>
    Number(value.toPrecision(12))

  for (const step of candidates) {
    if (step < targetStep) continue

    if (
      unit === 'COUNT' &&
      !Number.isInteger(step)
    ) continue

    if (
      unit === 'PERCENT' &&
      step * intervals > 100
    ) continue

    let lower = Math.max(
      0,
      Math.floor(low / step) * step,
    )

    let upper = lower + intervals * step

    if (unit === 'PERCENT' && upper > 100) {
      upper = 100
      lower = upper - intervals * step
    }

    if (
      lower > minimum + 1e-9 ||
      upper < maximum - 1e-9 ||
      upper < high - 1e-9
    ) continue

    return {
      domain: [clean(lower), clean(upper)],
      ticks: Array.from(
        { length: intervals + 1 },
        (_, index) =>
          clean(lower + index * step),
      ),
    }
  }

  return {
    domain: [minimum, maximum + padding],
    ticks: [minimum, maximum],
  }
}

export function MetricTrendChart({
  metrics,
  days,
  isLoading,
  hasErrors,
  onRetry,
}: MetricTrendChartProps) {
  const [primaryId, setPrimaryId] =
    useState('prsOpened')

  const [secondaryId, setSecondaryId] =
    useState('prsMerged')

  const primary =
    findMetric(metrics, primaryId)
    ?? metrics[0]

  const secondary =
    secondaryId !== 'none' &&
    secondaryId !== primary?.metricId
      ? findMetric(metrics, secondaryId)
      : undefined

  if (!primary) return null

  const dualAxis = Boolean(
    secondary &&
    primary.metricUnit !== secondary.metricUnit,
  )

  const chartData = days.map(day => ({
    date: day.date,

    primary:
      dailyMetric(day, primary.metricId)
        ?.currentValue ?? null,

    secondary: secondary
      ? dailyMetric(day, secondary.metricId)
          ?.currentValue ?? null
      : null,
  }))

  const primaryValues = chartData.map(
    row => row.primary,
  )

  const secondaryValues = chartData.map(
    row => row.secondary,
  )

  const primaryScale = axisScale(
    primary.metricUnit,
    secondary && !dualAxis
      ? [...primaryValues, ...secondaryValues]
      : primaryValues,
  )

  const secondaryScale = secondary
    ? axisScale(
        secondary.metricUnit,
        secondaryValues,
      )
    : undefined

  return (
    <ChartCard
      title="Daily Performance Trend"
      description="Explore daily movement across engineering metrics"
    >

      <div className="trend-controls">

        <label className="trend-select">
          <span>Primary metric</span>

          <select
            value={primary.metricId}
            onChange={event => {
              const value = event.target.value

              setPrimaryId(value)

              if (value === secondaryId) {
                setSecondaryId('none')
              }
            }}
          >
            {metrics.map(metric => (
              <option
                key={metric.metricId}
                value={metric.metricId}
              >
                {metric.metricName}
              </option>
            ))}
          </select>
        </label>

        <label className="trend-select">
          <span>Secondary metric</span>

          <select
            value={secondary?.metricId ?? 'none'}
            onChange={event =>
              setSecondaryId(event.target.value)
            }
          >
            <option value="none">None</option>

            {metrics
              .filter(metric =>
                metric.metricId !== primary.metricId
              )
              .map(metric => (
                <option
                  key={metric.metricId}
                  value={metric.metricId}
                >
                  {metric.metricName}
                </option>
              ))}
          </select>
        </label>

      </div>

      <div className="trend-legend">

        <span>
          <i data-series="primary" />
          {primary.metricName}
          {' · '}
          {unitLabels[primary.metricUnit]}
          {dualAxis ? ' · Left axis' : ''}
        </span>

        {secondary && (
          <span>
            <i data-series="secondary" />
            {secondary.metricName}
            {' · '}
            {unitLabels[secondary.metricUnit]}
            {dualAxis ? ' · Right axis' : ''}
          </span>
        )}

      </div>

      {isLoading && (
        <p className="trend-status" role="status">
          Loading daily analytical data...
        </p>
      )}

      {hasErrors && (
        <div className="trend-status">
          Some daily periods could not be retrieved.

          <button
            type="button"
            onClick={onRetry}
          >
            Retry
          </button>
        </div>
      )}

      <div className="trend-chart-scroll">

        <div className="trend-chart">

          <ResponsiveContainer
            width="100%"
            height={220}
          >
            <LineChart
              data={chartData}
              margin={{
                top: 8,
                right: 12,
                left: 4,
                bottom: 2,
              }}
            >

              <CartesianGrid
                stroke="var(--color-border)"
                strokeDasharray="3 3"
                vertical={false}
              />

              <XAxis
                dataKey="date"
                tickFormatter={formatDay}
                interval="preserveStartEnd"
                minTickGap={8}
                tick={{
                  fontSize: 11,
                  fill: 'var(--color-text-secondary)',
                }}
                tickLine={false}
                axisLine={{
                  stroke: 'var(--color-border)',
                }}
              height={42}
                tickMargin={6}
                label={{
                  value: 'Reporting Date (UTC)',
                  position: 'insideBottom',
                  offset: 0,
                  fill: 'var(--color-text-secondary)',
                  fontSize: 11,
                }}
              />

              <YAxis
                yAxisId="left"
                domain={primaryScale.domain}
                ticks={primaryScale.ticks}
                interval={0}
                allowDataOverflow
                allowDecimals={primary.metricUnit !== 'COUNT'}
                tickFormatter={value =>
                  formatNumber(Number(value))
                }
                tick={{
                  fontSize: 11,
                  fill: 'var(--chart-current)',
                }}
                tickLine={false}
                axisLine={false}
                width={76}
              tickMargin={8}
                label={{
                  value: unitLabels[primary.metricUnit],
                  angle: -90,
                  position: 'insideLeft',
                  fill: 'var(--chart-current)',
                  fontSize: 11,
                  fontWeight: 600,
                }}
              />

              {secondary && dualAxis && (
                <YAxis
                  yAxisId="right"
                  orientation="right"
                  domain={secondaryScale?.domain}
                  ticks={secondaryScale?.ticks}
                  interval={0}
                  allowDataOverflow
                  allowDecimals={secondary.metricUnit !== 'COUNT'}
                  tickFormatter={value =>
                    formatNumber(Number(value))
                  }
                  tick={{
                    fontSize: 11,
                    fill: 'var(--chart-secondary)',
                  }}
                  tickLine={false}
                  axisLine={false}
                  width={76}
                tickMargin={8}
                label={{
                  value: unitLabels[secondary.metricUnit],
                  angle: 90,
                  position: 'insideRight',
                  fill: 'var(--chart-secondary)',
                  fontSize: 11,
                  fontWeight: 600,
                }}
              />
              )}

              <Tooltip
                filterNull={false}
                shared={true}
                trigger="hover"
                isAnimationActive={false}
                offset={12}
                position={{ y: 12 }}
                allowEscapeViewBox={{
                  x: false,
                  y: false,
                }}
                wrapperStyle={{
                  pointerEvents: 'none',
                  zIndex: 10,
                }}
                cursor={{
                  stroke: 'var(--color-text-secondary)',
                  strokeWidth: 1,
                  strokeDasharray: '4 4',
                  strokeOpacity: 0.65,
                }}
                content={({ active, label }) => {
                  const day = days.find(
                    item => item.date === String(label),
                  )

                  if (!active || !day) return null

                  const selected = secondary
                    ? [primary, secondary]
                    : [primary]

                  return (
                    <div className="trend-tooltip">

                      <div className="trend-tooltip-header">
                        <strong>{formatDay(day.date)}</strong>
                        <span>DoD</span>
                      </div>

                      {day.state !== 'ACTUAL' && (
                        <small className="trend-tooltip-status">
                          {dayStateLabels[day.state]}
                        </small>
                      )}

                      {selected.map((metric, index) => {
                        const fact = dailyMetric(
                          day,
                          metric.metricId,
                        )

                        return (
                          <div
                            className="trend-tooltip-row"
                            key={metric.metricId}
                          >
                            <i
                              className="trend-tooltip-dot"
                              data-series={
                                index === 0
                                  ? 'primary'
                                  : 'secondary'
                              }
                            />

                            <span className="trend-tooltip-name">
                              {metric.metricName}
                            </span>

                            <strong className="numeric">
                              {formatMetricValue(
                                fact?.currentValue ?? null,
                                metric.metricUnit,
                              )}
                            </strong>

                            <span
                              className="trend-tooltip-change numeric"
                              data-tone={
                                fact
                                  ? getChangeTone(fact)
                                  : 'neutral'
                              }
                            >
                              {fact
                                ? formatMetricChange(fact)
                                : 'N/A'}
                            </span>
                          </div>
                        )
                      })}

                    </div>
                  )
                }}
              />

              <Line
                yAxisId="left"
                dataKey="primary"
                name={primary.metricName}
                type="linear"
                stroke="var(--chart-current)"
                strokeWidth={2}
                dot={{ r: 2.5 }}
                activeDot={{ r: 3.5 }}
                connectNulls={false}
                isAnimationActive={false}
              />

              {secondary && (
                <Line
                  yAxisId={
                    dualAxis ? 'right' : 'left'
                  }
                  dataKey="secondary"
                  name={secondary.metricName}
                  type="linear"
                  stroke="var(--chart-secondary)"
                  strokeDasharray="5 3"
                  strokeWidth={2}
                  dot={{ r: 2.5 }}
                  activeDot={{ r: 3.5 }}
                  connectNulls={false}
                  isAnimationActive={false}
                />
              )}

            </LineChart>
          </ResponsiveContainer>

        </div>
      </div>

      <p className="chart-note">
        Daily actuals · Estimated coverage · Adaptive axes.
        Missing observations appear as gaps.
        {dualAxis &&
          ' The two metrics use independent axis scales.'}
      </p>

    </ChartCard>
  )
}
