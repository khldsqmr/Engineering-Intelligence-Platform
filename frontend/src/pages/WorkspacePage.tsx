import { Layers3 } from 'lucide-react'

import { PageHeader } from '../components/layout/PageHeader'

interface WorkspacePageProps {
  category: string
  title: string
  description: string
}

export function WorkspacePage({
  category,
  title,
  description,
}: WorkspacePageProps) {
  return (
    <section className="workspace-page">

      <PageHeader
        category={category}
        title={title}
        description={description}
      />

      <div className="empty-state">

        <div className="empty-state-icon">
          <Layers3 size={28} />
        </div>

        <h2>Workspace under development</h2>

        <p>
          This workspace will be connected to EIP's
          analytical and intelligence services during
          the next implementation phase.
        </p>

      </div>

    </section>
  )
}
