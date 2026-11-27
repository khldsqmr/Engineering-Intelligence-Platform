import {
  Database,
  Layers,
  Sparkles,
  ShieldCheck,
  History,
  ArrowLeft,
  CalendarDays,
  BookOpen,
  Network,
  Target,
} from 'lucide-react'

import type { IntelligenceContext } from '../../../../types/context'

export type ContextNode =
  | 'sources'
  | 'assembly'
  | 'temporal'
  | 'semantic'
  | 'analytical'
  | 'relational'
  | 'quality'
  | 'historical'
  | 'intent'
  | 'generation'
  | 'assessment'
  | 'history'

export function ContextArchitecture({
  context,
  selected,
  onSelect,
}: {
  context: IntelligenceContext
  selected: ContextNode
  onSelect: (node: ContextNode) => void
}) {
  const layers = [
    {
      id: 'temporal' as const,
      title: 'Temporal',
      detail: 'Reporting periods',
      icon: CalendarDays,
    },
    {
      id: 'semantic' as const,
      title: 'Semantic',
      detail: `${context.semanticContext.length} definitions`,
      icon: BookOpen,
    },
    {
      id: 'analytical' as const,
      title: 'Analytical',
      detail: `${context.analyticalContext.length} evidence records`,
      icon: Database,
    },
    {
      id: 'relational' as const,
      title: 'Relational',
      detail: `${context.relationalContext.length} relationships`,
      icon: Network,
    },
    {
      id: 'quality' as const,
      title: 'Quality',
      detail: 'Coverage & limitations',
      icon: ShieldCheck,
    },
    {
      id: 'historical' as const,
      title: 'Historical',
      detail: context.historicalContext.length === 0
        ? 'No eligible prior insights'
        : `${context.historicalContext.length} prior insights available`,
      icon: History,
    },
    {
      id: 'intent' as const,
      title: 'User Intent',
      detail: 'Analysis objective',
      icon: Target,
    },
  ]

  const stages = [
    {
      id: 'sources' as const,
      number: '01',
      title: 'Information Sources',
      description: 'GitHub, metric registry and historical intelligence',
      icon: Database,
    },
    {
      id: 'assembly' as const,
      number: '02',
      title: 'Context Engineering',
      description: 'Assemble relevant information for the AI',
      icon: Layers,
    },
    {
      id: 'generation' as const,
      number: '03',
      title: 'AI Intelligence Generation',
      description: 'Observations, hypotheses and investigations',
      icon: Sparkles,
    },
    {
      id: 'assessment' as const,
      number: '04',
      title: 'Intelligence Assessment',
      description: 'Validation, AI evaluation and evidence confidence',
      icon: ShieldCheck,
    },
    {
      id: 'history' as const,
      number: '05',
      title: 'Intelligence History',
      description: 'Persist intelligence and retrieve eligible prior insights',
      icon: History,
    },
  ]

  return (
    <section className="context-card">

      <header className="context-card-header">
        <h2>Intelligence Architecture</h2>
        <p>From engineering data to evidence-grounded insights.</p>
      </header>

      <div className="context-flow">

        {stages.map((stage, index) => {
          const Icon = stage.icon

          const active =
            selected === stage.id ||
            (
              stage.id === 'assembly' &&
              layers.some(layer => layer.id === selected)
            )

          return (
            <div
              key={stage.id}
              className="context-stage"
              data-active={active}
              data-stage={stage.id}
              style={{ gridRow: index + 1 }}
            >
              <button
                type="button"
                className="context-stage-button"
                aria-pressed={selected === stage.id}
                onClick={() => onSelect(stage.id)}
              >
                <span className="context-stage-icon">
                  <Icon size={18} />
                </span>

                <span className="context-stage-copy">
                  <strong>
                    <small>{stage.number}</small>
                    {stage.title}
                  </strong>

                  <span>{stage.description}</span>
                </span>
              </button>

              {stage.id === 'assembly' && (
                <div className="context-layer-grid">
                  {layers.map(layer => {
                    const LayerIcon = layer.icon

                    return (
                      <button
                        type="button"
                        key={layer.id}
                        className="context-layer"
                        aria-pressed={selected === layer.id}
                        onClick={() => onSelect(layer.id)}
                      >
                        <LayerIcon size={13} />
                        <span>
                          <strong>{layer.title}</strong>
                          <small>{layer.detail}</small>
                        </span>
                      </button>
                    )
                  })}
                </div>
              )}
            </div>
          )
        })}

        <button
          type="button"
          className="context-feedback-rail"
          title="Explore historical intelligence reuse"
          aria-label="Explore historical intelligence reuse"
          onClick={() => onSelect('historical')}
        >
          <ArrowLeft size={14} />
          <span>Approved intelligence feedback</span>
        </button>

      </div>

      <div className="context-legend">
        <span><i /> Information flow</span>
        <span><i className="feedback" /> Historical reuse</span>
      </div>

      <p className="context-footnote">
        Select any stage or context layer to explore its contents.
        This is an architecture view, not a live execution trace.
      </p>

    </section>
  )
}
