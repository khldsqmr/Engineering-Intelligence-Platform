import type {
  AnalyticalMetric,
  MetricUnit,
} from '../types/analytics'

export type ChangeTone =
  | 'positive'
  | 'negative'
  | 'neutral'

function isAvailable(
  value: number | null,
): value is number {
  return value !== null && Number.isFinite(value)
}

export function formatNumber(
  value: number | null,
  decimals = 2,
): string {
  if (!isAvailable(value)) {
    return 'N/A'
  }

  return new Intl.NumberFormat('en-CA', {
    minimumFractionDigits: 0,
    maximumFractionDigits: decimals,
  }).format(value)
}

export function formatMetricValue(
  value: number | null,
  unit: MetricUnit,
): string {
  if (!isAvailable(value)) {
    return 'N/A'
  }

  switch (unit) {
    case 'COUNT':
      return formatNumber(value, 0)

    case 'HOURS':
      return `${formatNumber(value)} hrs`

    case 'PERCENT':
      return `${formatNumber(value)}%`

    case 'LINES':
      return `${formatNumber(value)} lines`

    case 'FILES':
      return `${formatNumber(value)} files`

    default:
      return formatNumber(value)
  }
}

export function getMetricChange(
  metric: AnalyticalMetric,
): number | null {
  return metric.metricUnit === 'PERCENT'
    ? metric.changeValue
    : metric.changePct
}

export function formatMetricChange(
  metric: AnalyticalMetric,
): string {
  const change = getMetricChange(metric)

  if (change === null || !Number.isFinite(change)) {
    return 'N/A'
  }

  const unit = metric.metricUnit === 'PERCENT'
    ? ' pp'
    : '%'

  const rounded = Number(change.toFixed(2))

  if (rounded === 0) {
    return `— 0${unit}`
  }

  const direction = rounded > 0 ? '▲' : '▼'

  return `${direction} ${formatNumber(Math.abs(rounded))}${unit}`
}

export function getChangeTone(
  metric: AnalyticalMetric,
): ChangeTone {
  const change = getMetricChange(metric)

  if (
    !isAvailable(change) ||
    change === 0 ||
    metric.performanceDirection === 'CONTEXT_DEPENDENT'
  ) {
    return 'neutral'
  }

  const improved =
    metric.performanceDirection === 'HIGHER_IS_BETTER'
      ? change > 0
      : change < 0

  return improved ? 'positive' : 'negative'
}

export function findMetric(
  metrics: AnalyticalMetric[],
  metricId: string,
): AnalyticalMetric | undefined {
  return metrics.find(
    metric => metric.metricId === metricId,
  )
}
