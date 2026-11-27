import { useId } from 'react'
import { Info } from 'lucide-react'

import type {
  AnalyticalMetric,
} from '../../types/analytics'

interface MetricTooltipProps {
  metric: AnalyticalMetric
  onExplore: () => void
}

export function MetricTooltip({
  metric,
  onExplore,
}: MetricTooltipProps) {
  const tooltipId = useId()

  return (
    <div className="metric-tooltip-container">

      <button
        type="button"
        className="metric-info-button"
        aria-label={`Explore ${metric.metricName}`}
        aria-describedby={tooltipId}
        aria-haspopup="dialog"
        onClick={onExplore}
      >
        <Info size={15} />
      </button>

      <div
        id={tooltipId}
        className="metric-tooltip"
        role="tooltip"
      >
        <strong>{metric.metricName}</strong>

        <p>{metric.metricDescription}</p>

        <span className="tooltip-hint">
          Click the information icon for full details
        </span>
      </div>

    </div>
  )
}
