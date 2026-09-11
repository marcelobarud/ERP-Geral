import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react'

import { getApiErrorMessage } from '../../services/httpClient'
import { pageIdForPath } from './types'
import {
  getAppearanceOverrides,
  resetAppearanceOverride,
  updateAppearanceOverride,
} from './api'
import type {
  AppearanceOverride,
  AppearanceOverridePayload,
  AppearancePageId,
  CustomizationProperties,
  CustomizationType,
} from './types'

export type CustomizationSemanticType =
  | 'TEXT' | 'ICON' | 'BUTTON' | 'INPUT' | 'SELECT' | 'TEXTAREA'
  | 'SURFACE' | 'BORDERED_SURFACE' | 'CARD' | 'TABLE' | 'TABLE_HEADER'
  | 'TABLE_CELL' | 'LINK' | 'BADGE' | 'PAGE'

export type EditorMode = 'select' | 'navigate'

export type CustomizationDescriptor = {
  key: string
  type: CustomizationType
  semanticType?: CustomizationSemanticType
  group?: string
  page?: AppearancePageId
  label: string
  persistable?: boolean
}

export type CustomizationSelection = CustomizationDescriptor & {
  element?: HTMLElement
  ancestors?: CustomizationSelection[]
}

type InspectorCandidate = CustomizationSelection & { element: HTMLElement }
type PendingValue = AppearanceOverride | null
type HistoryEntry = { key: string; hadPending: boolean; value: PendingValue | undefined; previousPersistable?: boolean }
type Rect = { top: number; left: number; width: number; height: number }

type VisualCustomizationContextValue = {
  active: boolean
  mode: EditorMode
  selected: CustomizationSelection | null
  dirty: boolean
  saving: boolean
  error: string | null
  start: () => void
  cancel: () => void
  save: () => Promise<void>
  undo: () => void
  canUndo: boolean
  resetSelected: () => void
  setMode: (mode: EditorMode) => void
  select: (descriptor: CustomizationSelection, element: HTMLElement) => void
  getProperties: (key: string) => CustomizationProperties
  updateProperty: (property: string, value: string | number) => void
}

const VisualCustomizationContext = createContext<VisualCustomizationContextValue | null>(null)

const EMPTY_CONTEXT: VisualCustomizationContextValue = {
  active: false, mode: 'select', selected: null, dirty: false, saving: false, error: null,
  start: () => undefined, cancel: () => undefined, save: async () => undefined,
  undo: () => undefined, canUndo: false, resetSelected: () => undefined,
  setMode: () => undefined, select: () => undefined, getProperties: () => ({}), updateProperty: () => undefined,
}

const SEMANTIC_LABELS: Record<CustomizationSemanticType, string> = {
  TEXT: 'Texto', ICON: 'Ícone', BUTTON: 'Botão', INPUT: 'Campo', SELECT: 'Seleção', TEXTAREA: 'Texto longo',
  SURFACE: 'Superfície', BORDERED_SURFACE: 'Superfície com borda', CARD: 'Card', TABLE: 'Tabela',
  TABLE_HEADER: 'Cabeçalho de tabela', TABLE_CELL: 'Célula de tabela', LINK: 'Link', BADGE: 'Badge', PAGE: 'Página',
}

const PROPERTY_LABELS: Record<string, string> = {
  cor: 'Cor', cor_fundo: 'Fundo', cor_borda: 'Borda', cor_texto: 'Texto',
  cor_cabecalho: 'Fundo do cabeçalho', cor_texto_cabecalho: 'Texto do cabeçalho',
  cor_corpo: 'Fundo do corpo', cor_texto_corpo: 'Texto do corpo', raio: 'Arredondamento', peso: 'Peso', tamanho: 'Tamanho',
}

const MANAGED_STYLE_PROPERTIES = [
  'color', 'fontWeight', 'fontSize', 'backgroundColor', 'borderColor', 'borderRadius',
  '--custom-table-header-bg', '--custom-table-header-text', '--custom-table-body-bg', '--custom-table-body-text', '--custom-table-border',
] as const

function canonicalTypeForSemantic(type: CustomizationSemanticType): CustomizationType {
  if (type === 'BUTTON' || type === 'BADGE') return 'BUTTON'
  if (type === 'INPUT' || type === 'SELECT' || type === 'TEXTAREA') return 'INPUT'
  if (type === 'SURFACE' || type === 'BORDERED_SURFACE' || type === 'CARD') return 'SURFACE'
  if (type === 'TABLE' || type === 'TABLE_HEADER' || type === 'TABLE_CELL') return 'TABLE'
  if (type === 'PAGE') return 'PAGE'
  return 'TEXT'
}

function semanticForCanonical(type: CustomizationType): CustomizationSemanticType {
  if (type === 'BUTTON') return 'BUTTON'
  if (type === 'INPUT') return 'INPUT'
  if (type === 'SURFACE') return 'SURFACE'
  if (type === 'TABLE') return 'TABLE'
  return type
}

function slug(value: string, fallback = 'elemento'): string {
  const normalized = value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '')
  return (normalized || fallback).slice(0, 48)
}

function keyPartFromElement(element: HTMLElement): string | null {
  const dataRole = element.dataset.customizationRole
  if (dataRole) return slug(dataRole)
  const fieldId = element.getAttribute('id') || element.getAttribute('name')
  if (fieldId) return slug(fieldId)
  const ariaLabel = element.getAttribute('aria-label')
  if (ariaLabel) return slug(ariaLabel)
  const stableClass = Array.from(element.classList).find((item) => !/^(active|open|selected|loading|error|disabled)$/.test(item))
  if (stableClass) return slug(stableClass)
  return null
}

function ownText(element: HTMLElement): string {
  return Array.from(element.childNodes).filter((node) => node.nodeType === Node.TEXT_NODE).map((node) => node.textContent?.trim() ?? '').filter(Boolean).join(' ')
}

function elementLabel(element: HTMLElement): string {
  const ariaLabel = element.getAttribute('aria-label')
  if (ariaLabel) return ariaLabel
  const labelledBy = element.getAttribute('aria-labelledby')
  if (labelledBy) {
    const labelledText = labelledBy.split(/\s+/).map((id) => document.getElementById(id)?.textContent?.trim()).filter(Boolean).join(' ')
    if (labelledText) return labelledText
  }
  if (element instanceof HTMLInputElement || element instanceof HTMLTextAreaElement || element instanceof HTMLSelectElement) {
    if (element.id) {
      const label = Array.from(document.querySelectorAll('label')).find((candidate) => candidate.htmlFor === element.id)
      if (label?.textContent?.trim()) return label.textContent.trim()
    }
    if (element.getAttribute('placeholder')) return element.getAttribute('placeholder') as string
  }
  const text = (ownText(element) || element.textContent || '').replace(/\s+/g, ' ').trim()
  if (text.length <= 80) return text || element.tagName.toLowerCase()
  return keyPartFromElement(element) || element.tagName.toLowerCase()
}

function isIgnored(element: Element): boolean {
  return Boolean(element.closest('[data-customization-ignore]'))
}

function hasVisualPresentation(element: HTMLElement): boolean {
  const style = window.getComputedStyle(element)
  const background = style.backgroundColor
  return (Boolean(background) && background !== 'rgba(0, 0, 0, 0)' && background !== 'transparent')
    || (Boolean(style.borderStyle) && style.borderStyle !== 'none')
    || (Boolean(style.boxShadow) && style.boxShadow !== 'none')
    || (Boolean(style.borderRadius) && style.borderRadius !== '0px')
}

function inferredSemanticType(element: HTMLElement): CustomizationSemanticType | null {
  const tag = element.tagName.toLowerCase()
  const role = element.getAttribute('role')
  const className = typeof element.className === 'string' ? element.className : ''
  const classLower = className.toLowerCase()
  if (tag === 'main') return 'PAGE'
  if (tag === 'button' || role === 'button') return 'BUTTON'
  if (tag === 'input') return 'INPUT'
  if (tag === 'select') return 'SELECT'
  if (tag === 'textarea') return 'TEXTAREA'
  if (tag === 'table') return 'TABLE'
  if (tag === 'th') return 'TABLE_HEADER'
  if (tag === 'td') return 'TABLE_CELL'
  if (tag === 'a' || role === 'link') return 'LINK'
  if (tag === 'svg' || tag === 'img' || role === 'img' || classLower.includes('icon')) return 'ICON'
  if (classLower.includes('badge') || classLower.includes('chip') || classLower.includes('status-')) return 'BADGE'
  if (ownText(element)) return 'TEXT'
  if (hasVisualPresentation(element)) {
    if (classLower.includes('card') || classLower.includes('panel') || classLower.includes('box')) return 'CARD'
    if (window.getComputedStyle(element).borderStyle && window.getComputedStyle(element).borderStyle !== 'none') return 'BORDERED_SURFACE'
    return 'SURFACE'
  }
  return null
}

function tableColumnPart(element: HTMLElement): { base: string; column: string } | null {
  const cell = element.closest<HTMLElement>('th,td')
  const table = cell?.closest<HTMLTableElement>('table')
  if (!cell || !table) return null
  const row = cell.parentElement
  const index = row ? Array.from(row.children).indexOf(cell) : -1
  if (index < 0) return null
  const base = table.dataset.customizationKey || `${pageIdForPath(window.location.pathname)}.table`
  const header = table.querySelector('thead')?.rows[0]?.cells[index]?.textContent?.trim() || `coluna-${index + 1}`
  return { base, column: slug(header, `coluna-${index + 1}`) }
}

function regionPart(element: HTMLElement): string {
  const region = element.closest<HTMLElement>('nav,aside,dialog,[role="dialog"],section,form')
  if (!region) return 'pagina'
  const aria = region.getAttribute('aria-label') || region.getAttribute('aria-labelledby')
  return slug(aria || keyPartFromElement(region) || region.tagName.toLowerCase())
}

function autoKeyForElement(element: HTMLElement, semanticType: CustomizationSemanticType): { key: string; group: string; persistable: boolean } {
  const page = pageIdForPath(window.location.pathname)
  const explicitParent = element.parentElement?.closest<HTMLElement>('[data-customization-key]')
  const table = tableColumnPart(element)
  if (table) {
    const suffix = semanticType === 'TABLE_HEADER' ? 'header' : semanticType === 'TABLE_CELL' ? 'cell' : semanticType === 'TEXT' ? 'text' : semanticType.toLowerCase()
    return { key: `${table.base}.column.${table.column}.${suffix}`, group: 'data-table', persistable: true }
  }
  const field = keyPartFromElement(element)
  if (explicitParent) {
    const textPart = ownText(element)
    const suffix = field || (textPart ? slug(textPart) : semanticType.toLowerCase())
    return { key: `${explicitParent.dataset.customizationKey}.${suffix}`, group: explicitParent.dataset.customizationGroup || slug(suffix), persistable: true }
  }
  const label = elementLabel(element)
  const part = field || (semanticType === 'TEXT' || semanticType === 'LINK' || semanticType === 'BADGE' ? slug(label) : null)
  const group = regionPart(element)
  if (!part) return { key: `${page}.${group}.${semanticType.toLowerCase()}`, group, persistable: false }
  return { key: `${page}.${group}.${semanticType.toLowerCase()}.${part}`, group, persistable: true }
}

function candidateForElement(element: HTMLElement): InspectorCandidate | null {
  if (isIgnored(element)) return null
  const explicitType = element.dataset.customizationType as CustomizationType | undefined
  const explicitKey = element.dataset.customizationKey
  const semanticType = (element.dataset.customizationSemantic as CustomizationSemanticType | undefined) || (explicitType ? semanticForCanonical(explicitType) : inferredSemanticType(element))
  if (!semanticType) return null
  const auto = explicitKey ? null : autoKeyForElement(element, semanticType)
  const key = explicitKey || auto?.key
  if (!key) return null
  return {
    key,
    type: explicitType || canonicalTypeForSemantic(semanticType),
    semanticType,
    group: element.dataset.customizationGroup || auto?.group,
    page: (element.dataset.customizationPage as AppearancePageId | undefined) || pageIdForPath(window.location.pathname),
    label: element.dataset.customizationLabel || elementLabel(element),
    persistable: explicitKey ? true : auto?.persistable,
    element,
  }
}

function withAncestors(candidate: InspectorCandidate): InspectorCandidate {
  const ancestors: CustomizationSelection[] = []
  let parent = candidate.element.parentElement
  while (parent && parent !== document.body) {
    const parentCandidate = candidateForElement(parent)
    if (parentCandidate && parentCandidate.key !== candidate.key) ancestors.push({ ...parentCandidate, element: parentCandidate.element })
    parent = parent.parentElement
  }
  return { ...candidate, ancestors }
}

// oxlint-disable-next-line react/only-export-components
export function resolveCustomizationCandidate(target: EventTarget | null): InspectorCandidate | null {
  let element: HTMLElement | null = target instanceof HTMLElement ? target : null
  if (!element && target instanceof Element) element = target.closest<HTMLElement>('*')
  while (element && element !== document.body) {
    if (isIgnored(element)) return null
    const candidate = candidateForElement(element)
    if (candidate) return withAncestors(candidate)
    element = element.parentElement
  }
  return null
}

function styleFromProperties(semanticType: CustomizationSemanticType, properties: CustomizationProperties): Record<string, string | number> {
  const style: Record<string, string | number> = {}
  const value = (key: string) => properties[key]
  if (semanticType === 'TEXT' || semanticType === 'ICON' || semanticType === 'LINK') {
    if (typeof value('cor') === 'string') style.color = value('cor') as string
    if (typeof value('peso') === 'number') style.fontWeight = value('peso') as number
    if (typeof value('tamanho') === 'number') style.fontSize = `${value('tamanho')}px`
  }
  if (['BUTTON', 'BADGE', 'INPUT', 'SELECT', 'TEXTAREA', 'SURFACE', 'BORDERED_SURFACE', 'CARD'].includes(semanticType)) {
    if (typeof value('cor_fundo') === 'string') style.backgroundColor = value('cor_fundo') as string
    if (typeof value('cor_texto') === 'string') style.color = value('cor_texto') as string
    if (typeof value('cor_borda') === 'string') style.borderColor = value('cor_borda') as string
    if (typeof value('raio') === 'number') style.borderRadius = `${value('raio')}px`
  }
  if (semanticType === 'TABLE') {
    if (typeof value('cor_cabecalho') === 'string') style['--custom-table-header-bg'] = value('cor_cabecalho') as string
    if (typeof value('cor_texto_cabecalho') === 'string') style['--custom-table-header-text'] = value('cor_texto_cabecalho') as string
    if (typeof value('cor_corpo') === 'string') style['--custom-table-body-bg'] = value('cor_corpo') as string
    if (typeof value('cor_texto_corpo') === 'string') style['--custom-table-body-text'] = value('cor_texto_corpo') as string
    if (typeof value('cor_borda') === 'string') style['--custom-table-border'] = value('cor_borda') as string
  }
  if (semanticType === 'TABLE_HEADER') {
    if (typeof value('cor_cabecalho') === 'string') style.backgroundColor = value('cor_cabecalho') as string
    if (typeof value('cor_texto_cabecalho') === 'string') style.color = value('cor_texto_cabecalho') as string
    if (typeof value('cor_borda') === 'string') style.borderColor = value('cor_borda') as string
  }
  if (semanticType === 'TABLE_CELL') {
    if (typeof value('cor_corpo') === 'string') style.backgroundColor = value('cor_corpo') as string
    if (typeof value('cor_texto_corpo') === 'string') style.color = value('cor_texto_corpo') as string
    if (typeof value('cor_borda') === 'string') style.borderColor = value('cor_borda') as string
  }
  if (semanticType === 'PAGE' && typeof value('cor_fundo') === 'string') style.backgroundColor = value('cor_fundo') as string
  return style
}

function propertyDefaults(type: CustomizationSemanticType): Record<string, string | number> {
  if (type === 'TEXT') return { cor: '#1E293B', peso: 400, tamanho: 16 }
  if (type === 'ICON') return { cor: '#2F5975' }
  if (type === 'LINK') return { cor: '#2F5975', peso: 400 }
  if (type === 'BUTTON' || type === 'BADGE') return { cor_fundo: '#487A98', cor_texto: '#FFFFFF', cor_borda: '#487A98', raio: 12 }
  if (type === 'INPUT' || type === 'SELECT' || type === 'TEXTAREA') return { cor_fundo: '#FFFFFF', cor_texto: '#1E293B', cor_borda: '#DCE7EE', raio: 12 }
  if (type === 'TABLE') return { cor_cabecalho: '#FFFFFF', cor_texto_cabecalho: '#2F5975', cor_corpo: '#FFFFFF', cor_texto_corpo: '#1E293B', cor_borda: '#DCE7EE' }
  if (type === 'TABLE_HEADER') return { cor_cabecalho: '#FFFFFF', cor_texto_cabecalho: '#2F5975', cor_borda: '#DCE7EE' }
  if (type === 'TABLE_CELL') return { cor_corpo: '#FFFFFF', cor_texto_corpo: '#1E293B', cor_borda: '#DCE7EE' }
  if (type === 'PAGE') return { cor_fundo: '#EEF4F8' }
  return { cor_fundo: '#FFFFFF', cor_borda: '#DCE7EE', raio: 16 }
}

function applyStyle(element: HTMLElement, semanticType: CustomizationSemanticType, properties: CustomizationProperties, originals: WeakMap<HTMLElement, Record<string, string>>) {
  if (!originals.has(element)) {
    const original: Record<string, string> = {}
    for (const property of MANAGED_STYLE_PROPERTIES) original[property] = element.style.getPropertyValue(property)
    originals.set(element, original)
  }
  const original = originals.get(element) as Record<string, string>
  for (const property of MANAGED_STYLE_PROPERTIES) element.style.setProperty(property, original[property])
  for (const [property, value] of Object.entries(styleFromProperties(semanticType, properties))) element.style.setProperty(property, String(value))
}

function restoreStyle(element: HTMLElement, originals: WeakMap<HTMLElement, Record<string, string>>) {
  const original = originals.get(element)
  if (!original) return
  for (const property of MANAGED_STYLE_PROPERTIES) element.style.setProperty(property, original[property])
  element.removeAttribute('data-visual-customization-auto-key')
  element.removeAttribute('data-visual-customization-auto-semantic')
}

function propertyToCss(property: string): string {
  if (property.startsWith('--')) return property
  return property.replace(/[A-Z]/g, (letter) => `-${letter.toLowerCase()}`)
}

function overrideCss(saved: Record<string, AppearanceOverride>, pending: Record<string, PendingValue>): string {
  const values = new Map<string, AppearanceOverride | null>(Object.entries(saved).map(([key, value]) => [key, value]))
  for (const [key, value] of Object.entries(pending)) values.set(key, value)
  return Array.from(values.entries()).flatMap(([key, value]) => {
    if (!value) return []
    const safeKey = key.replace(/"/g, '')
    const declarations = Object.entries(styleFromProperties(semanticForCanonical(value.customization_type), value.properties))
      .map(([property, propertyValue]) => `${propertyToCss(property)}:${String(propertyValue)};`).join('')
    return declarations ? `[data-visual-customization-auto-key="${safeKey}"]{${declarations}}` : []
  }).join('\n')
}

export function VisualCustomizationProvider({ children }: { children: ReactNode }) {
  const [saved, setSaved] = useState<Record<string, AppearanceOverride>>({})
  const [pending, setPending] = useState<Record<string, PendingValue>>({})
  const [history, setHistory] = useState<HistoryEntry[]>([])
  const [active, setActive] = useState(false)
  const [mode, setMode] = useState<EditorMode>('select')
  const [selected, setSelected] = useState<CustomizationSelection | null>(null)
  const [hovered, setHovered] = useState<InspectorCandidate | null>(null)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [hoverRect, setHoverRect] = useState<Rect | null>(null)
  const [selectedRect, setSelectedRect] = useState<Rect | null>(null)
  const hoverElement = useRef<HTMLElement | null>(null)
  const selectedElement = useRef<HTMLElement | null>(null)
  const autoStyled = useRef(new Set<HTMLElement>())
  const originalStyles = useRef(new WeakMap<HTMLElement, Record<string, string>>())
  const nonPersistablePending = useRef(new Set<string>())
  const persistedOverrideCss = useMemo(() => overrideCss(saved, pending), [pending, saved])

  useEffect(() => {
    let mounted = true
    void getAppearanceOverrides().then(({ items }) => {
      if (mounted) setSaved(Object.fromEntries(items.map((item) => [item.customization_key, item])))
    }).catch((loadError: unknown) => {
      if (mounted) setError(getApiErrorMessage(loadError, 'Não foi possível carregar a personalização visual.'))
    })
    return () => { mounted = false }
  }, [])

  const rectFor = useCallback((element: HTMLElement): Rect => {
    const rect = element.getBoundingClientRect()
    return { top: rect.top, left: rect.left, width: rect.width, height: rect.height }
  }, [])

  const clearEditorState = useCallback(() => {
    hoverElement.current?.removeAttribute('data-visual-customization-hovered')
    selectedElement.current?.removeAttribute('data-visual-customization-selected')
    hoverElement.current = null
    selectedElement.current = null
    setHovered(null)
    setHoverRect(null)
    setSelectedRect(null)
  }, [])

  const restoreAutoStyles = useCallback(() => {
    for (const element of autoStyled.current) restoreStyle(element, originalStyles.current)
    autoStyled.current.clear()
  }, [])

  const syncAutoStyles = useCallback(() => {
    restoreAutoStyles()
    const overrideKeys = new Set([...Object.keys(saved), ...Object.keys(pending)])
    if (!overrideKeys.size || !document.body) return
    const nodes = document.querySelectorAll<HTMLElement>('main, main *, aside, aside *, header, header *, nav, nav *, [role="dialog"], [role="dialog"] *')
    for (const element of nodes) {
      if (isIgnored(element) || element.hasAttribute('data-customization-key')) continue
      const candidate = candidateForElement(element)
      if (!candidate || candidate.element !== element || !overrideKeys.has(candidate.key)) continue
      const value = Object.prototype.hasOwnProperty.call(pending, candidate.key) ? pending[candidate.key] : saved[candidate.key]
      if (value === null || !value) continue
      const semanticType = candidate.semanticType || semanticForCanonical(candidate.type)
      applyStyle(element, semanticType, value.properties, originalStyles.current)
      element.dataset.visualCustomizationAutoKey = candidate.key
      element.dataset.visualCustomizationAutoSemantic = semanticType
      autoStyled.current.add(element)
    }
  }, [pending, restoreAutoStyles, saved])

  useEffect(() => {
    syncAutoStyles()
    if (!Object.keys(saved).length && !Object.keys(pending).length) return undefined
    let timer: number | undefined
    const observer = new MutationObserver(() => {
      if (timer !== undefined) return
      timer = window.setTimeout(() => { timer = undefined; syncAutoStyles() }, 50)
    })
    if (document.body) observer.observe(document.body, { childList: true, subtree: true })
    return () => { observer.disconnect(); if (timer !== undefined) window.clearTimeout(timer); restoreAutoStyles() }
  }, [pending, restoreAutoStyles, saved, syncAutoStyles])

  const selectCandidate = useCallback((candidate: InspectorCandidate) => {
    selectedElement.current?.removeAttribute('data-visual-customization-selected')
    selectedElement.current = candidate.element
    candidate.element.setAttribute('data-visual-customization-selected', 'true')
    const next = withAncestors(candidate)
    setSelected(next)
    setSelectedRect(rectFor(candidate.element))
  }, [rectFor])

  useEffect(() => {
    // oxlint-disable-next-line react/set-state-in-effect
    if (!active) { clearEditorState(); return undefined }
    const onPointerMove = (event: PointerEvent) => {
      if (mode !== 'select' || (event.target instanceof Element && isIgnored(event.target))) return
      const candidate = resolveCustomizationCandidate(event.target)
      if (!candidate) {
        hoverElement.current?.removeAttribute('data-visual-customization-hovered')
        hoverElement.current = null
        setHovered(null)
        setHoverRect(null)
        return
      }
      if (hoverElement.current !== candidate.element) {
        hoverElement.current?.removeAttribute('data-visual-customization-hovered')
        hoverElement.current = candidate.element
        candidate.element.setAttribute('data-visual-customization-hovered', 'true')
        setHovered(candidate)
      }
      setHoverRect(rectFor(candidate.element))
    }
    const onPointerOut = (event: PointerEvent) => {
      if (event.relatedTarget instanceof Node) return
      hoverElement.current?.removeAttribute('data-visual-customization-hovered')
      hoverElement.current = null
      setHovered(null)
      setHoverRect(null)
    }
    const onClick = (event: MouseEvent) => {
      if (mode !== 'select' || (event.target instanceof Element && isIgnored(event.target))) return
      const candidate = resolveCustomizationCandidate(event.target)
      if (!candidate) return
      event.preventDefault()
      event.stopPropagation()
      selectCandidate(candidate)
    }
    const refresh = () => {
      if (hoverElement.current) setHoverRect(rectFor(hoverElement.current))
      if (selectedElement.current) setSelectedRect(rectFor(selectedElement.current))
    }
    document.addEventListener('pointermove', onPointerMove, true)
    document.addEventListener('pointerout', onPointerOut, true)
    document.addEventListener('click', onClick, true)
    window.addEventListener('scroll', refresh, true)
    window.addEventListener('resize', refresh)
    return () => {
      document.removeEventListener('pointermove', onPointerMove, true)
      document.removeEventListener('pointerout', onPointerOut, true)
      document.removeEventListener('click', onClick, true)
      window.removeEventListener('scroll', refresh, true)
      window.removeEventListener('resize', refresh)
      clearEditorState()
    }
  }, [active, clearEditorState, mode, rectFor, selectCandidate])

  useEffect(() => {
    if (!active) return undefined
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key !== 'Escape') return
      event.preventDefault()
      nonPersistablePending.current.clear(); setPending({}); setHistory([]); setSelected(null); setActive(false)
    }
    document.addEventListener('keydown', onKeyDown, true)
    return () => document.removeEventListener('keydown', onKeyDown, true)
  }, [active])

  const start = useCallback(() => { setError(null); nonPersistablePending.current.clear(); setMode('select'); setActive(true); setSelected(null) }, [])
  const cancel = useCallback(() => { nonPersistablePending.current.clear(); setPending({}); setHistory([]); setSelected(null); setActive(false) }, [])
  const getProperties = useCallback((key: string): CustomizationProperties => Object.prototype.hasOwnProperty.call(pending, key) ? pending[key]?.properties ?? {} : saved[key]?.properties ?? {}, [pending, saved])

  const select = useCallback((descriptor: CustomizationSelection, element: HTMLElement) => {
    selectCandidate(withAncestors({ ...descriptor, element, semanticType: descriptor.semanticType || semanticForCanonical(descriptor.type) }))
  }, [selectCandidate])

  const updateProperty = useCallback((property: string, value: string | number) => {
    if (!selected) return
    const key = selected.key
    const semanticType = selected.semanticType || semanticForCanonical(selected.type)
    const hadPending = Object.prototype.hasOwnProperty.call(pending, key)
    const current = hadPending ? pending[key] : saved[key] ?? null
    const next: AppearanceOverride = {
      id: current?.id ?? 0, customization_key: key, customization_type: canonicalTypeForSemantic(semanticType),
      customization_group: selected.group ?? current?.customization_group ?? null, pagina: selected.page ?? current?.pagina ?? null,
      properties: { ...(current?.properties ?? {}), [property]: value },
    }
    setHistory((entries) => [...entries, { key, hadPending, value: hadPending ? pending[key] : undefined, previousPersistable: !nonPersistablePending.current.has(key) }])
    setPending((currentPending) => ({ ...currentPending, [key]: next }))
    if (selected.persistable === false) nonPersistablePending.current.add(key)
    else nonPersistablePending.current.delete(key)
    if (selected.element && !selected.element.hasAttribute('data-customization-key')) {
      // oxlint-disable-next-line react/immutability
      selected.element.dataset.visualCustomizationAutoKey = key
      selected.element.dataset.visualCustomizationAutoSemantic = semanticType
      applyStyle(selected.element, semanticType, next.properties, originalStyles.current)
    }
  }, [pending, saved, selected])

  const undo = useCallback(() => {
    const previous = history.at(-1)
    if (!previous) return
    setHistory((entries) => entries.slice(0, -1))
    setPending((currentPending) => {
      const next = { ...currentPending }
      if (previous.hadPending) {
        next[previous.key] = previous.value as PendingValue
        if (previous.previousPersistable === false) nonPersistablePending.current.add(previous.key)
        else nonPersistablePending.current.delete(previous.key)
      } else {
        delete next[previous.key]
        nonPersistablePending.current.delete(previous.key)
      }
      return next
    })
  }, [history])

  const resetSelected = useCallback(() => {
    if (!selected) return
    const key = selected.key
    const hadPending = Object.prototype.hasOwnProperty.call(pending, key)
    setHistory((entries) => [...entries, { key, hadPending, value: hadPending ? pending[key] : undefined, previousPersistable: !nonPersistablePending.current.has(key) }])
    setPending((currentPending) => ({ ...currentPending, [key]: null }))
    nonPersistablePending.current.delete(key)
    if (selected.element && !selected.element.hasAttribute('data-customization-key')) restoreStyle(selected.element, originalStyles.current)
  }, [pending, selected])

  const save = useCallback(async () => {
    setSaving(true); setError(null)
    try {
      const nextSaved = { ...saved }
      if (Object.keys(pending).some((key) => nonPersistablePending.current.has(key))) throw new Error('Este elemento ainda precisa de uma identidade semântica estável.')
      for (const [key, value] of Object.entries(pending)) {
        if (value === null) { await resetAppearanceOverride(key); delete nextSaved[key] } else {
          nextSaved[key] = await updateAppearanceOverride(key, { customization_type: value.customization_type, customization_group: value.customization_group, pagina: value.pagina, properties: value.properties } satisfies AppearanceOverridePayload)
        }
      }
      nonPersistablePending.current.clear(); setSaved(nextSaved); setPending({}); setHistory([]); setActive(false); setSelected(null)
    } catch (saveError: unknown) { setError(getApiErrorMessage(saveError, 'Não foi possível salvar a personalização visual.')) } finally { setSaving(false) }
  }, [pending, saved])

  const value = useMemo<VisualCustomizationContextValue>(() => ({ active, mode, selected, dirty: Object.keys(pending).length > 0, saving, error, start, cancel, save, undo, canUndo: history.length > 0, resetSelected, setMode, select, getProperties, updateProperty }), [active, cancel, error, getProperties, history.length, mode, pending, resetSelected, save, saving, select, selected, start, undo, updateProperty])

  return <VisualCustomizationContext.Provider value={value}><style data-customization-ignore="true" data-visual-customization-styles>{persistedOverrideCss}</style>{children}<VisualCustomizationPanel hovered={hovered} hoverRect={hoverRect} selectedRect={selectedRect} /></VisualCustomizationContext.Provider>
}

// oxlint-disable-next-line react/only-export-components
export function useVisualCustomization(): VisualCustomizationContextValue { return useContext(VisualCustomizationContext) ?? EMPTY_CONTEXT }

// oxlint-disable-next-line react/only-export-components
export function useCustomizable(descriptor: CustomizationDescriptor) {
  const { getProperties } = useVisualCustomization()
  const semanticType = descriptor.semanticType || semanticForCanonical(descriptor.type)
  return { 'data-customization-key': descriptor.key, 'data-customization-type': descriptor.type, 'data-customization-semantic': semanticType, 'data-customization-group': descriptor.group, 'data-customization-page': descriptor.page, 'data-customization-label': descriptor.label, style: styleFromProperties(semanticType, getProperties(descriptor.key)) }
}

function VisualCustomizationPanel({ hovered, hoverRect, selectedRect }: { hovered: InspectorCandidate | null; hoverRect: Rect | null; selectedRect: Rect | null }) {
  const { active, mode, selected, dirty, saving, error, cancel, save, undo, canUndo, resetSelected, setMode, getProperties, updateProperty, select } = useVisualCustomization()
  if (!active) return null
  const semanticType = selected?.semanticType || (selected ? semanticForCanonical(selected.type) : null)
  const defaults = semanticType ? propertyDefaults(semanticType) : {}
  const properties = selected ? getProperties(selected.key) : {}
  const selectAncestor = (ancestor: CustomizationSelection) => { if (ancestor.element) select(ancestor, ancestor.element) }

  return <>
    {hoverRect ? <div className="visual-editor-overlay visual-editor-overlay-hover" data-customization-ignore="true" style={{ top: hoverRect.top, left: hoverRect.left, width: hoverRect.width, height: hoverRect.height }}><span>{hovered?.label} · {hovered ? SEMANTIC_LABELS[hovered.semanticType || semanticForCanonical(hovered.type)] : ''}</span></div> : null}
    {selectedRect && (!hovered || hovered.element !== selected?.element) ? <div className="visual-editor-overlay visual-editor-overlay-selected" data-customization-ignore="true" style={{ top: selectedRect.top, left: selectedRect.left, width: selectedRect.width, height: selectedRect.height }} /> : null}
    <div className="visual-editor-bar" data-customization-ignore="true" role="status" aria-label="Personalização visual ativa">
      <strong>🎨 Personalização ativa</strong>
      <span>{selected ? selected.label : mode === 'navigate' ? 'Modo Navegar: use o ERP normalmente.' : 'Modo Selecionar: aponte e clique em um elemento visual.'}</span>
      <div className="visual-editor-mode" aria-label="Modo do editor"><span>Modo</span><button className="button button-secondary" type="button" aria-pressed={mode === 'select'} onClick={() => setMode('select')}>Selecionar</button><button className="button button-secondary" type="button" aria-pressed={mode === 'navigate'} onClick={() => setMode('navigate')}>Navegar</button></div>
      <div className="visual-editor-actions"><button className="button button-secondary" type="button" onClick={undo} disabled={!canUndo || saving}>Desfazer</button><button className="button button-secondary" type="button" onClick={cancel} disabled={saving}>Cancelar</button><button className="button button-primary" type="button" onClick={() => void save()} disabled={!dirty || saving}>{saving ? 'Salvando...' : 'Salvar'}</button></div>
    </div>
    {error ? <div className="visual-editor-error" data-customization-ignore="true" role="alert">{error}</div> : null}
    {selected ? <aside className="visual-editor-panel" data-customization-ignore="true" aria-label="Propriedades do elemento selecionado"><p className="eyebrow">Elemento selecionado</p><h2>{selected.label}</h2><p className="visual-editor-type">Tipo: {SEMANTIC_LABELS[semanticType || 'TEXT']}</p>{selected.persistable === false ? <p className="visual-editor-warning">Prévia disponível. Para salvar, este componente precisa de uma identidade semântica estável.</p> : null}{selected.ancestors?.length ? <div className="visual-editor-hierarchy"><span>Dentro de:</span>{selected.ancestors.slice(0, 4).map((ancestor) => <button type="button" key={`${ancestor.key}-${ancestor.label}`} onClick={() => selectAncestor(ancestor)}>↑ {ancestor.label} · {SEMANTIC_LABELS[ancestor.semanticType || semanticForCanonical(ancestor.type)]}</button>)}</div> : null}<div className="visual-editor-fields">{Object.keys(defaults).map((property) => { const value = properties[property] ?? defaults[property]; if (property === 'peso') return <label className="form-field" key={property}>{PROPERTY_LABELS[property]}<select value={String(value)} onChange={(event) => updateProperty(property, Number(event.target.value))}><option value="400">Normal</option><option value="500">Médio</option><option value="600">Semibold</option><option value="700">Negrito</option><option value="800">Extra forte</option></select></label>; if (property === 'tamanho') return <label className="form-field" key={property}>{PROPERTY_LABELS[property]}<select value={String(value)} onChange={(event) => updateProperty(property, Number(event.target.value))}>{[12, 14, 16, 18, 20, 24, 28, 32, 36].map((size) => <option value={size} key={size}>{size}px</option>)}</select></label>; if (property === 'raio') return <label className="form-field" key={property}>{PROPERTY_LABELS[property]}<select value={String(value)} onChange={(event) => updateProperty(property, Number(event.target.value))}>{[0, 4, 8, 12, 16, 20, 24].map((radius) => <option value={radius} key={radius}>{radius}px</option>)}</select></label>; return <label className="visual-editor-color-field" key={property}>{PROPERTY_LABELS[property]}<input aria-label={PROPERTY_LABELS[property]} type="color" value={String(value)} onChange={(event) => updateProperty(property, event.target.value.toUpperCase())} /><code>{String(value)}</code></label> })}</div><button className="button button-secondary" type="button" onClick={resetSelected}>Restaurar este elemento</button></aside> : null}
  </>
}
