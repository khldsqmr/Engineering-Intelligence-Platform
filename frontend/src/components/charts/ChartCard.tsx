import type { ReactNode } from 'react'

import {
  MetadataLabels,
} from '../metadata/MetadataLabels'

import type {
  InformationType,
} from '../metadata/MetadataLabels'

import './charts.css'

interface ChartCardProps {
  title: string
  description?: string
  source?: string
  informationType?: InformationType
  children: ReactNode
}

export function ChartCard({
  title,
  description,
  source = 'GitHub',
  informationType = 'Fact',
  children,
}: ChartCardProps) {
  return (
    <article className="chart-card">

      <header className="chart-card-header">

        <div>
          <h2>{title}</h2>

          {description && (
            <p>{description}</p>
          )}
        </div>

        <MetadataLabels
          source={source}
          informationType={informationType}
        />

      </header>

      <div className="chart-card-content">
        {children}
      </div>

    </article>
  )
}
