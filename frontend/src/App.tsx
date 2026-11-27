import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
} from 'react-router-dom'

import {
  AppShell,
} from './components/layout/AppShell'

import {
  navigationGroups,
} from './components/layout/navigation'

import {
  WorkspacePage,
} from './pages/WorkspacePage'

import {
  ExecutiveOverviewPage,
} from './features/analytics/executive_overview/ExecutiveOverviewPage'

import { PerformanceManagementPage } from './features/analytics/performance_management/PerformanceManagementPage'

import { EngineeringLifecyclePage } from './features/analytics/engineering_lifecycle/EngineeringLifecyclePage'

import { AIInsightsPage } from './features/intelligence/ai_insights/AIInsightsPage'

import { ContextExplorerPage } from './features/intelligence/context_explorer/ContextExplorerPage'

import { IntelligenceHistoryPage } from './features/intelligence/intelligence_history/IntelligenceHistoryPage'

import { DataQualityPage } from './features/governance/data_quality/DataQualityPage'

import { MetricCatalogPage } from './features/knowledge_reference/metric_catalog/MetricCatalogPage'

import { GlossaryMethodologyPage } from './features/knowledge_reference/glossary_methodology/GlossaryMethodologyPage'

import './App.css'

function App() {
  return (
    <BrowserRouter>
      <Routes>

        <Route element={<AppShell />}>

          {navigationGroups.flatMap(group =>
            group.items.map(item => (
              <Route
                key={item.path}
                path={item.path}
                element={
                  item.path === '/'
                    ? <ExecutiveOverviewPage />
                    : item.path === '/performance'
                      ? <PerformanceManagementPage />
                      : item.path === '/lifecycle'
                        ? <EngineeringLifecyclePage />
                        : item.path === '/intelligence'
                          ? <AIInsightsPage />
                          : item.path === '/context'
                            ? <ContextExplorerPage />
                            : item.path === '/history'
                              ? <IntelligenceHistoryPage />
                                : item.path === '/data-quality'
                                  ? <DataQualityPage />
                                  : item.path === '/metrics'
                                    ? <MetricCatalogPage />
                                    : item.path === '/glossary'
                                      ? <GlossaryMethodologyPage />
                    : (
                      <WorkspacePage
                        category={group.label}
                        title={item.label}
                        description={item.description}
                      />
                    )
                }
              />
            )),
          )}

          <Route
            path="*"
            element={<Navigate to="/" replace />}
          />

        </Route>

      </Routes>
    </BrowserRouter>
  )
}

export default App
