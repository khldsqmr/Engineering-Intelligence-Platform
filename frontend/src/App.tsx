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
