import { useState, type ReactNode } from 'react'

import { getNavigationGroups, type RouteDefinition } from '../app/routes'
import { useHealthStatus } from '../app/useHealthStatus'
import { Sidebar } from './Sidebar'
import { useAppearance } from '../features/settings/AppearanceContext'
import { appearanceLabels } from '../features/settings/types'
import { pageIdForPath } from '../features/settings/types'
import { pageAppearanceCssVars } from '../features/settings/theme'
import type { PageAppearanceTheme } from '../features/settings/types'
import { useCustomizable } from '../features/settings/VisualCustomizationContext'
import { useAuth } from '../features/auth/AuthContext'
import { resolveBackendAssetUrl } from '../services/httpClient'

type AppLayoutProps = {
  route: RouteDefinition
  onNavigate: (path: string) => void
  children: ReactNode
  pageTheme?: PageAppearanceTheme
}

function HealthIndicator() {
  const { status, retry } = useHealthStatus()

  if (status === 'loading') {
    return (
      <span className="health-indicator health-loading" role="status">
        <span className="health-dot" aria-hidden="true" />
        Verificando API
      </span>
    )
  }

  if (status === 'offline') {
    return (
      <button
        className="health-indicator health-offline"
        type="button"
        onClick={() => void retry()}
        title="Tentar conectar novamente"
      >
        <span className="health-dot" aria-hidden="true" />
        API indisponível
      </button>
    )
  }

  return (
    <span className="health-indicator health-online" role="status">
      <span className="health-dot" aria-hidden="true" />
      API online
    </span>
  )
}

export function AppLayout({ route, onNavigate, children, pageTheme }: AppLayoutProps) {
  const { preview } = useAppearance()
  const { user, logout } = useAuth()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const pageCustomization = useCustomizable({
    key: `${pageIdForPath(route.path)}.page`,
    type: 'PAGE',
    page: pageIdForPath(route.path),
    label: route.label,
  })

  const navigate = (path: string) => {
    onNavigate(path)
    setSidebarOpen(false)
  }

  return (
    <div className="app-frame">
      <Sidebar
        groups={getNavigationGroups(appearanceLabels(preview))}
        brandName={preview.nome_sistema}
        logoUrl={resolveBackendAssetUrl(preview.logo_url)}
        currentPath={route.path === '/not-found' ? '' : route.path}
        isOpen={sidebarOpen}
        onNavigate={navigate}
      />
      {sidebarOpen ? (
        <button
          className="sidebar-backdrop"
          type="button"
          aria-label="Fechar menu"
          onClick={() => setSidebarOpen(false)}
        />
      ) : null}

      <div className="app-shell">
        <header className="topbar">
          <div className="topbar-leading">
            <button
              className="menu-button"
              type="button"
              aria-label={sidebarOpen ? 'Fechar menu' : 'Abrir menu'}
              aria-expanded={sidebarOpen}
              onClick={() => setSidebarOpen((isOpen) => !isOpen)}
            >
              <span aria-hidden="true">☰</span>
            </button>
            <div>
              <p className="topbar-kicker">Área administrativa</p>
              <strong>{route.label}</strong>
            </div>
          </div>
          <div className="topbar-actions">
            {user ? <span className="topbar-user">{user.nome}</span> : null}
            {user ? <button className="text-button" type="button" onClick={() => void logout()}>Sair</button> : null}
            <HealthIndicator />
          </div>
        </header>

        <main
          className="main-content"
          {...pageCustomization}
          style={{
            ...(pageTheme ? pageAppearanceCssVars(pageTheme) : {}),
            ...pageCustomization.style,
          }}
        >
          {children}
        </main>
      </div>
    </div>
  )
}
