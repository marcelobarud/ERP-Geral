import { useEffect, useId, useRef, type ReactNode } from 'react'
import { useCustomizable } from '../features/settings/VisualCustomizationContext'
import { actionIcons, iconSizes, iconStroke } from '../app/iconography'
import { focusPageFallback, focusWithoutScroll, getFocusableElements } from './focusManagement'

const CloseIcon = actionIcons.close

const modalStack: symbol[] = []
let modalScrollLockDepth = 0
let previousBodyOverflow = ''

type ModalProps = {
  title: string
  description?: string
  children: ReactNode
  onClose: () => void
  size?: 'small' | 'large'
  initialFocusRef?: { current: HTMLElement | null }
}

export function Modal({
  title,
  description,
  children,
  onClose,
  size = 'small',
  initialFocusRef,
}: ModalProps) {
  const modalRef = useRef<HTMLElement>(null)
  const closeButtonRef = useRef<HTMLButtonElement>(null)
  const modalStackEntryRef = useRef<symbol>(Symbol('modal'))
  const onCloseRef = useRef(onClose)
  const titleId = useId()
  const descriptionId = useId()
  const surfaceCustomization = useCustomizable({ key: 'global.modal.surface', type: 'SURFACE', group: 'modal', label: title })
  const titleCustomization = useCustomizable({ key: 'global.modal.title', type: 'TEXT', group: 'modal-title', label: title })
  const closeCustomization = useCustomizable({ key: 'global.modal.close', type: 'BUTTON', group: 'modal-action', label: 'Fechar' })

  useEffect(() => {
    onCloseRef.current = onClose
  }, [onClose])

  useEffect(() => {
    const opener = document.activeElement instanceof HTMLElement ? document.activeElement : null
    const modalStackEntry = modalStackEntryRef.current

    const modal = modalRef.current
    const requestedFocus = initialFocusRef?.current
    const firstField = modal?.querySelector<HTMLElement>(
      'input:not([disabled]):not([type="hidden"]), select:not([disabled]), textarea:not([disabled]), [autofocus]',
    )
    const requestedFocusIsUsable = requestedFocus
      && modal?.contains(requestedFocus)
      && !requestedFocus.hidden
      && requestedFocus.getAttribute('aria-hidden') !== 'true'
      && !requestedFocus.hasAttribute('disabled')
    focusWithoutScroll(requestedFocusIsUsable ? requestedFocus : firstField ?? getFocusableElements(modal ?? document.body)[0] ?? modal)

    modalStack.push(modalStackEntry)
    if (modalScrollLockDepth === 0) {
      previousBodyOverflow = document.body.style.overflow
      document.body.style.overflow = 'hidden'
    }
    modalScrollLockDepth += 1

    const handleKeyDown = (event: KeyboardEvent) => {
      if (modalStack[modalStack.length - 1] !== modalStackEntry) return

      if (event.key === 'Escape') {
        event.preventDefault()
        event.stopPropagation()
        onCloseRef.current()
        return
      }

      if (event.key !== 'Tab' || !modal) return

      const focusableElements = getFocusableElements(modal)
      if (focusableElements.length === 0) {
        event.preventDefault()
        focusWithoutScroll(modal)
        return
      }

      const first = focusableElements[0]
      const last = focusableElements[focusableElements.length - 1]
      const activeElement = document.activeElement

      if (event.shiftKey && (activeElement === first || !modal.contains(activeElement))) {
        event.preventDefault()
        focusWithoutScroll(last)
      } else if (!event.shiftKey && (activeElement === last || !modal.contains(activeElement))) {
        event.preventDefault()
        focusWithoutScroll(first)
      }
    }

    document.addEventListener('keydown', handleKeyDown)

    return () => {
      document.removeEventListener('keydown', handleKeyDown)

      const stackIndex = modalStack.indexOf(modalStackEntry)
      const wasTopmost = stackIndex === modalStack.length - 1
      if (stackIndex >= 0) modalStack.splice(stackIndex, 1)
      modalScrollLockDepth -= 1
      if (modalScrollLockDepth === 0) document.body.style.overflow = previousBodyOverflow

      if (!wasTopmost) return

      if (opener && opener.isConnected && !opener.hasAttribute('disabled') && opener.getAttribute('aria-hidden') !== 'true') {
        focusWithoutScroll(opener)
      } else {
        focusPageFallback()
      }
    }
  }, [initialFocusRef])

  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={onClose}>
      <section
        ref={modalRef}
        className={`modal-card modal-card-${size}`}
        {...surfaceCustomization}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={description ? descriptionId : undefined}
        tabIndex={-1}
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="modal-header">
          <div>
            <h2 id={titleId} {...titleCustomization}>{title}</h2>
            {description ? <p id={descriptionId}>{description}</p> : null}
          </div>
          <button
            className="icon-button"
            ref={closeButtonRef}
            {...closeCustomization}
            type="button"
            aria-label="Fechar"
            onClick={onClose}
          >
            <CloseIcon size={iconSizes.action} stroke={iconStroke} aria-hidden="true" focusable="false" />
          </button>
        </div>
        {children}
      </section>
    </div>
  )
}
