import { useEffect, useRef, useState } from 'react'

import type { NavigationGroup } from '../app/routes'
import { useCustomizable } from '../features/settings/VisualCustomizationContext'

type SidebarProps = {
  groups: NavigationGroup[]
  currentPath: string
  isOpen: boolean
  onNavigate: (path: string) => void
  onClose: () => void
  brandName: string
  logoUrl: string | null
}

function isActivePath(currentPath: string, itemPath: string): boolean {
  if (itemPath === '/') return currentPath === '/'
  return currentPath === itemPath
}

export function Sidebar({
  groups,
  currentPath,
  isOpen,
  onNavigate,
  onClose,
  brandName,
  logoUrl,
}: SidebarProps) {
  const sidebarRef = useRef<HTMLElement>(null)
  const closeButtonRef = useRef<HTMLButtonElement>(null)
  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>({})
  const [isMobile, setIsMobile] = useState(
    () => window.matchMedia?.('(max-width: 900px)').matches ?? false,
  )
  const sidebarCustomization = useCustomizable({ key: 'global.sidebar', type: 'SURFACE', group: 'sidebar', label: 'Barra lateral' })
  const brandCustomization = useCustomizable({ key: 'global.sidebar.brand', type: 'TEXT', group: 'sidebar-brand', label: brandName })
  const noteCustomization = useCustomizable({ key: 'global.sidebar.note', type: 'SURFACE', group: 'sidebar-note', label: 'Nota da barra lateral' })

  useEffect(() => {
    const mediaQuery = window.matchMedia?.('(max-width: 900px)')
    if (!mediaQuery) return

    const handleChange = (event: MediaQueryListEvent) => setIsMobile(event.matches)
    mediaQuery.addEventListener?.('change', handleChange)
    return () => mediaQuery.removeEventListener?.('change', handleChange)
  }, [])

  useEffect(() => {
    if (!isOpen || !isMobile) return

    closeButtonRef.current?.focus()

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault()
        onClose()
        return
      }
      if (event.key !== 'Tab') return

      const focusable = Array.from(
        sidebarRef.current?.querySelectorAll<HTMLElement>('a[href], button:not([disabled])') ?? [],
      )
      if (!focusable.length) return

      const first = focusable[0]
      const last = focusable[focusable.length - 1]
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault()
        last.focus()
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault()
        first.focus()
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [isMobile, isOpen, onClose])

  const isGroupActive = (group: NavigationGroup) => group.items.some((item) => isActivePath(currentPath, item.path))
  const isGroupExpanded = (group: NavigationGroup) => group.collapsible ? Boolean(expandedGroups[group.label] || isGroupActive(group)) : true

  return (
    <aside
      className={`sidebar ${isOpen ? 'sidebar-open' : ''}`}
      id="primary-navigation"
      ref={sidebarRef}
      aria-hidden={isMobile && !isOpen ? true : undefined}
      inert={isMobile && !isOpen ? true : undefined}
      {...sidebarCustomization}
    >
      <div className="brand-lockup" {...brandCustomization}>
        {logoUrl ? <img className="brand-logo" data-customization-role="logo" src={logoUrl} alt="Logo do sistema" /> : <span className="brand-mark" data-customization-role="logo" aria-hidden="true">C</span>}
        <div>
          <strong data-customization-role="name">{brandName}</strong>
          <span data-customization-role="subtitle">Gestão simples</span>
        </div>
      </div>

      <div className="sidebar-mobile-header">
        <span>Menu principal</span>
        <button className="sidebar-close" ref={closeButtonRef} type="button" aria-label="Fechar menu" onClick={onClose}>
          ×
        </button>
      </div>

      <nav className="sidebar-nav" aria-label="Navegação principal">
        {groups.map((group) => (
          <div className={`nav-group ${group.collapsible ? 'nav-group-collapsible' : ''}`} key={group.label}>
            {group.collapsible ? (
              <button
                className="nav-group-toggle"
                type="button"
                aria-expanded={isGroupExpanded(group)}
                aria-controls={`nav-group-${group.label.toLowerCase().replace(/[^a-z0-9]+/g, '-')}`}
                onClick={() => setExpandedGroups((current) => ({ ...current, [group.label]: !isGroupExpanded(group) }))}
              >
                <span className="nav-group-label">{group.label}</span>
                <span className="nav-group-chevron" aria-hidden="true">⌄</span>
              </button>
            ) : <p className="nav-group-label">{group.label}</p>}
            {isGroupExpanded(group) ? (
              <div className="nav-group-items" id={`nav-group-${group.label.toLowerCase().replace(/[^a-z0-9]+/g, '-')}`}>
                {group.items.map((item) => {
                  const active = isActivePath(currentPath, item.path)

                  return (
                    <a
                      className={`nav-link ${active ? 'nav-link-active' : ''}`}
                      href={item.path}
                      key={item.path}
                      aria-current={active ? 'page' : undefined}
                      onClick={(event) => {
                        event.preventDefault()
                        onNavigate(item.path)
                      }}
                    >
                      <span className="nav-icon" aria-hidden="true">
                        {item.icon}
                      </span>
                      <span>{item.label}</span>
                    </a>
                  )
                })}
              </div>
            ) : null}
          </div>
        ))}
      </nav>

      <div className="sidebar-note" {...noteCustomization}>
        <span className="sidebar-note-dot" aria-hidden="true" />
        <div>
          <strong>Fundação V1</strong>
          <span>Seu espaço de gestão está tomando forma.</span>
        </div>
      </div>
    </aside>
  )
}
