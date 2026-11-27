import type { ReactNode } from 'react'

interface PageHeaderProps {
  category?: string
  title: string
  description?: string
  actions?: ReactNode
}

export function PageHeader({
  category,
  title,
  description,
  actions,
}: PageHeaderProps) {
  return (
    <div className="page-header">

      <div className="page-heading">

        {category && (
          <p className="page-category">
            {category}
          </p>
        )}

        <h1>{title}</h1>

        {description && (
          <p className="page-description">
            {description}
          </p>
        )}

      </div>

      {actions && (
        <div className="page-actions">
          {actions}
        </div>
      )}

    </div>
  )
}
