import { useEffect, useState } from 'react'

import {
  Activity,
  Circle,
  GitBranch,
  PanelLeftClose,
  PanelLeftOpen,
} from 'lucide-react'

import {
  NavLink,
  Outlet,
  useLocation,
} from 'react-router-dom'

import { AppearanceControls } from './AppearanceControls'

import {
  navigationGroups,
  navigationItems,
} from './navigation'

import { getHealth } from '../../services/healthService'
import type { HealthResponse } from '../../types/health'


export function AppShell() {
  const [collapsed, setCollapsed] = useState(false)

  const [health, setHealth] =
    useState<HealthResponse | null>(null)

  const [error, setError] = useState(false)

  const location = useLocation()

  const currentPage = navigationItems.find(
    item => item.path === location.pathname,
  )

  useEffect(() => {
    const controller = new AbortController()

    getHealth(controller.signal)
      .then(result => {
        if (!controller.signal.aborted) {
          setHealth(result)
          setError(false)
        }
      })
      .catch(() => {
        if (!controller.signal.aborted) {
          setError(true)
        }
      })

    return () => controller.abort()
  }, [])

  return (
    <div
      className="app-shell"
      data-collapsed={collapsed}
    >
      {/* 01. Persistent sidebar */}

      <aside className="sidebar">

        <NavLink
          to="/"
          className="brand"
          aria-label="Engineering Intelligence Platform home"
        >
          <div className="brand-icon">
            <Activity size={25} />
          </div>

          {!collapsed && (
            <div className="brand-details">
              <div className="brand-name">EIP</div>

              <div className="brand-subtitle">
                Engineering Intelligence Platform
              </div>
            </div>
          )}
        </NavLink>

        <nav
          className="sidebar-navigation"
          aria-label="Main navigation"
        >
          {navigationGroups.map(group => (
            <section
              className="navigation-group"
              key={group.label}
            >
              {!collapsed && (
                <p className="navigation-label">
                  {group.label}
                </p>
              )}

              {group.items.map(item => {
                const Icon = item.icon

                return (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    end={item.path === '/'}
                    title={item.label}
                    aria-label={item.label}
                    className={({ isActive }) =>
                      `navigation-item ${
                        isActive ? 'active' : ''
                      }`
                    }
                  >
                    <Icon
                      size={18}
                      aria-hidden="true"
                    />

                    {!collapsed && (
                      <span>{item.label}</span>
                    )}
                  </NavLink>
                )
              })}
            </section>
          ))}
        </nav>

        <div className="sidebar-footer">
          <GitBranch size={17} aria-hidden="true" />

          {!collapsed && (
            <span>GitHub-powered intelligence</span>
          )}
        </div>

      </aside>

      {/* 02. Main workspace */}

      <div className="workspace">

        <header className="workspace-header">

          <div className="header-navigation">

            <button
              className="icon-button"
              aria-label={
                collapsed
                  ? 'Expand sidebar'
                  : 'Collapse sidebar'
              }
              aria-expanded={!collapsed}
              title={
                collapsed
                  ? 'Expand sidebar'
                  : 'Collapse sidebar'
              }
              onClick={() =>
                setCollapsed(previous => !previous)
              }
            >
              {collapsed
                ? <PanelLeftOpen size={20} />
                : <PanelLeftClose size={20} />}
            </button>

            <div className="header-divider" />

            <div className="header-breadcrumb">
              <span>Workspace</span>
              <span>/</span>

              <strong>
                {currentPage?.label || 'Overview'}
              </strong>
            </div>

          </div>

          {/* 03. Connectivity and appearance */}

          <div className="header-actions">

            <div
              className="health-indicator"
              data-state={
                error
                  ? 'error'
                  : health
                    ? 'connected'
                    : 'loading'
              }
              role="status"
              title={health
                ? `API version: ${health.version}`
                : 'Backend connectivity'}
            >
              <Circle
                size={8}
                fill="currentColor"
                aria-hidden="true"
              />

              <span>
                {error
                  ? 'API unavailable'
                  : health
                    ? `API: ${health.status}`
                    : 'Connecting'}
              </span>
            </div>

            <div className="header-divider" />

            <AppearanceControls />

          </div>

        </header>

        {/* 04. Routed workspace content */}

        <main className="workspace-content">
          <Outlet />
        </main>

      </div>
    </div>
  )
}
