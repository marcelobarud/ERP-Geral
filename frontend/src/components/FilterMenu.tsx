import { useEffect, useId, useRef, type ReactNode } from 'react'

import { FilterActions } from './FilterActions'
import { focusWithoutScroll, getFocusableElements } from './focusManagement'

type FilterMenuProps = {
  activeCount: number
  canClear: boolean
  children: ReactNode
  onApply: () => void
  onClear: () => void
  onClose: () => void
  onToggle: () => void
  open: boolean
}

export function FilterMenu({
  activeCount,
  canClear,
  children,
  onApply,
  onClear,
  onClose,
  onToggle,
  open,
}: FilterMenuProps) {
  const menuRef = useRef<HTMLDivElement>(null)
  const panelRef = useRef<HTMLDivElement>(null)
  const triggerRef = useRef<HTMLButtonElement>(null)
  const wasOpenRef = useRef(false)
  const panelId = useId()

  useEffect(() => {
    if (open) {
      focusWithoutScroll(getFocusableElements(panelRef.current ?? document.body)[0] ?? panelRef.current)
    } else if (wasOpenRef.current) {
      focusWithoutScroll(triggerRef.current)
    }
    wasOpenRef.current = open
  }, [open])

  useEffect(() => {
    if (!open) return

    const handlePointerDown = (event: PointerEvent) => {
      if (event.target instanceof Node && !menuRef.current?.contains(event.target)) {
        onClose()
      }
    }
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault()
        event.stopPropagation()
        onClose()
      }
    }

    document.addEventListener('pointerdown', handlePointerDown)
    document.addEventListener('keydown', handleKeyDown)
    return () => {
      document.removeEventListener('pointerdown', handlePointerDown)
      document.removeEventListener('keydown', handleKeyDown)
    }
  }, [onClose, open])

  return (
    <div className="filter-menu-wrap" ref={menuRef}>
      <button
        className="filter-menu-trigger"
        ref={triggerRef}
        type="button"
        aria-expanded={open}
        aria-haspopup="dialog"
        aria-controls={panelId}
        onClick={onToggle}
      >
        Filtros{activeCount > 0 ? ` (${activeCount})` : ''}
        <span className="filter-menu-chevron" aria-hidden="true">▾</span>
      </button>
      {open ? (
        <div ref={panelRef} className="filter-menu-panel" id={panelId} role="dialog" aria-label="Filtros detalhados">
          <div className="filter-menu-heading">Filtros detalhados</div>
          <div className="filter-menu-fields">{children}</div>
          <FilterActions canClear={canClear} onApply={onApply} onClear={onClear} />
        </div>
      ) : null}
    </div>
  )
}
