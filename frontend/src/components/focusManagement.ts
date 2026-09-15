const focusableSelector = [
  'a[href]',
  'button:not([disabled])',
  'input:not([disabled]):not([type="hidden"])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  '[tabindex]:not([tabindex="-1"])',
].join(', ')

export function getFocusableElements(container: ParentNode): HTMLElement[] {
  return Array.from(container.querySelectorAll<HTMLElement>(focusableSelector)).filter(
    (element) => !element.hidden && element.getAttribute('aria-hidden') !== 'true',
  )
}

export function focusWithoutScroll(element: HTMLElement | null) {
  element?.focus({ preventScroll: true })
}

export function focusPageFallback() {
  const main = document.querySelector<HTMLElement>('main')
  const fallback = main ? getFocusableElements(main)[0] : null
  focusWithoutScroll(fallback ?? document.body)
}
