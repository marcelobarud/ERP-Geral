import { useCallback, useEffect, useRef, useState, type ReactNode } from 'react'

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
  activeModules?: ReadonlySet<string>
  canManageUsers?: boolean
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

  if (status === 'degraded') {
    return (
      <button
        className="health-indicator health-degraded"
        type="button"
        onClick={() => void retry()}
        title="O backend está ativo, mas há uma dependência operacional degradada"
      >
        <span className="health-dot" aria-hidden="true" />
        API degradada
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

export function AppLayout({ route, onNavigate, children, pageTheme, activeModules, canManageUsers = true }: AppLayoutProps) {
  const { preview } = useAppearance()
  const { user, logout } = useAuth()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const menuButtonRef = useRef<HTMLButtonElement>(null)
  const sidebarWasOpen = useRef(false)
  const closeSidebar = useCallback(() => setSidebarOpen(false), [])
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

  useEffect(() => {
    if (!sidebarOpen && sidebarWasOpen.current && window.matchMedia?.('(max-width: 900px)').matches) {
      menuButtonRef.current?.focus()
    }
    sidebarWasOpen.current = sidebarOpen
  }, [sidebarOpen])

  useEffect(() => {
    if (!sidebarOpen || !window.matchMedia?.('(max-width: 900px)').matches) return

    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.body.style.overflow = previousOverflow
    }
  }, [sidebarOpen])

  return (
    <div className="app-frame">
      <Sidebar
        groups={getNavigationGroups(appearanceLabels(preview), activeModules, canManageUsers)}
        brandName={preview.nome_sistema}
        logoUrl={resolveBackendAssetUrl(preview.logo_url)}
        currentPath={route.path === '/not-found' ? '' : route.path}
        isOpen={sidebarOpen}
        onNavigate={navigate}
        onClose={closeSidebar}
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
              ref={menuButtonRef}
              type="button"
              aria-label={sidebarOpen ? 'Fechar menu' : 'Abrir menu'}
              aria-expanded={sidebarOpen}
              onClick={() => setSidebarOpen((isOpen) => !isOpen)}
            >
              <span aria-hidden="true">☰</span>
            </button>
            <p className="topbar-kicker">Área administrativa</p>
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
