import {
  BookOpen,
  GitPullRequest,
  History,
  Layers3,
  LayoutDashboard,
  Library,
  ShieldCheck,
  Sparkles,
  Table2,
} from 'lucide-react'

export const navigationGroups = [
  {
    label: 'Analytics',
    items: [
      {
        path: '/',
        label: 'Executive Overview',
        description:
          'Monitor engineering activity, collaboration and delivery.',
        icon: LayoutDashboard,
      },
      {
        path: '/lifecycle',
        label: 'Engineering Lifecycle',
        description:
          'Explore engineering activity, review engagement, delivery and code changes.',
        icon: GitPullRequest,
      },
      {
        path: '/performance',
        label: 'Performance Management',
        description:
          'Track daily metric movements, DoD changes and weekly performance.',
        icon: Table2,
      },
    ],
  },
  {
    label: 'Intelligence',
    items: [
      {
        path: '/intelligence',
        label: 'AI Insights',
        description:
          'Explore governed observations, hypotheses and supporting evidence.',
        icon: Sparkles,
      },
      {
        path: '/context',
        label: 'Context Explorer',
        description:
          'Inspect the analytical and semantic context supplied to the AI.',
        icon: Layers3,
      },
      {
        path: '/history',
        label: 'Intelligence History',
        description:
          'Review persisted intelligence, evaluations and governance decisions.',
        icon: History,
      },
    ],
  },
  {
    label: 'Governance',
    items: [
      {
        path: '/data-quality',
        label: 'Data Quality',
        description:
          'Understand source coverage, enrichment and analytical limitations.',
        icon: ShieldCheck,
      },
    ],
  },
  {
    label: 'Knowledge & Reference',
    items: [
      {
        path: '/metrics',
        label: 'Metric Catalog',
        description:
          'Understand metric definitions, calculations and analytical value.',
        icon: BookOpen,
      },
      {
        path: '/glossary',
        label: 'Glossary & Methodology',
        description:
          'Learn the terminology and methodologies powering EIP.',
        icon: Library,
      },
    ],
  },
]

export const navigationItems = navigationGroups.flatMap(
  group => group.items,
)
